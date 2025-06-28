import os
import json
import logging
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone
import mysql.connector
from geo_localizacion_ai import geocodificar_coordenadas, enriquecer_metadata_con_openai
from deducir_filtros_con_gpt import deducir_filtros_con_gpt

# Configurar logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/regeneracion.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

load_dotenv()

# Conexiones
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pinecone_client = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
pinecone_index = pinecone_client.Index(os.getenv("PINECONE_INDEX_NAME"))

db = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)
cursor = db.cursor(dictionary=True)

# Obtener todas las notas con pinecone_id válido
cursor.execute("SELECT * FROM notas WHERE pinecone_id IS NOT NULL")
notas = cursor.fetchall()

print(f"Procesando {len(notas)} notas para regenerar vectores en Pinecone...")
logging.info(f"Iniciando regeneración de {len(notas)} notas")

for nota in notas:
    try:
        texto = nota["texto"]
        pinecone_id = nota["pinecone_id"]
        user_id = nota["user_id"]
        lat = float(nota["latitud"]) if nota["latitud"] else None
        lon = float(nota["longitud"]) if nota["longitud"] else None

        # Enriquecer ubicación textual si hay coordenadas
        ubicacion_resuelta = geocodificar_coordenadas(lat, lon) if lat and lon else nota["ubicacion_textual"]

        # Enriquecer con OpenAI
        enriquecido = enriquecer_metadata_con_openai(texto, ubicacion_resuelta)

        # Deducir filtros automáticos para mejorar búsquedas futuras
        filtros_sugeridos = deducir_filtros_con_gpt(texto)
        logging.info(f"Filtros sugeridos para nota {nota['id']}: {filtros_sugeridos}")

        # Generar nuevo embedding
        embedding = openai_client.embeddings.create(
            input=texto,
            model="text-embedding-3-small"
        ).data[0].embedding

        # Armar metadata segura para Pinecone
        metadata = {
            "user_id": str(user_id),
            "fecha": str(nota["fecha"]),
            "hora": str(nota["hora"]),
            "emocion": enriquecido.get("emocion"),
            "categoria": enriquecido.get("categoria"),
            "tags": enriquecido.get("tags"),
            "titulo": enriquecido.get("titulo"),
            "resumen": enriquecido.get("resumen"),
            "ubicacion": ubicacion_resuelta,
            "modelo_embedding": "text-embedding-3-small"
        }
        if lat is not None:
            metadata["latitud"] = lat
        if lon is not None:
            metadata["longitud"] = lon

        # Subir a Pinecone
        pinecone_index.upsert([(pinecone_id, embedding, metadata)])
        print(f"✅ Vector actualizado: {pinecone_id}")
        logging.info(f"Vector actualizado: {pinecone_id}")

        # Actualizar también en MySQL
        cursor.execute("""
            UPDATE notas
            SET emocion = %s, categoria = %s, tags = %s, resumen = %s, ubicacion_textual = %s
            WHERE id = %s
        """, (
            enriquecido.get("emocion"),
            enriquecido.get("categoria"),
            json.dumps(enriquecido.get("tags")),
            enriquecido.get("resumen"),
            ubicacion_resuelta,
            nota["id"]
        ))
        db.commit()

    except Exception as e:
        error_msg = f"❌ Error procesando nota ID {nota['id']} (pinecone_id: {nota['pinecone_id']}): {e}"
        print(error_msg)
        logging.error(error_msg)

cursor.close()
db.close()
logging.info("\n🎉 Regeneración completa.")
print("\n🎉 Regeneración completa.")
