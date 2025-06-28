from fastapi import FastAPI, Query
from pydantic import BaseModel
from datetime import datetime
import os
from dotenv import load_dotenv
from pinecone import Pinecone
from openai import OpenAI
import json
from utils.db import get_db_connection
from fastapi.middleware.cors import CORSMiddleware
from gpt_utils import completar_campos_con_openai, deducir_ubicacion_textual_desde_coordenadas
from datetime import datetime, timedelta
from mapa import router as mapa_router
from geo_localizacion_ai import geocodificar_coordenadas, enriquecer_metadata_con_openai
from deducir_filtros_con_gpt import deducir_filtros_con_gpt

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))

app = FastAPI()

# Configurar CORS
#app.add_middleware(
#    CORSMiddleware,
#    allow_origins=["*"],
#    allow_methods=["*"],
#    allow_headers=["*"],
#)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



class NotaRequest(BaseModel):
    user_email: str
    texto: str
    emocion: str = None
    tags: list[str] = []
    categoria: str = None
    ubicacion_textual: str = None
    latitud: float = None
    longitud: float = None


@app.post("/guardar-nota")
def guardar_nota(data: NotaRequest):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    now = datetime.now()
    fecha = now.date()
    hora = now.time()

    # Buscar o crear usuario
    cursor.execute("SELECT id FROM usuarios WHERE email = %s", (data.user_email,))
    user = cursor.fetchone()
    if not user:
        cursor.execute("INSERT INTO usuarios (nombre, email) VALUES (%s, %s)", (data.user_email, data.user_email))
        db.commit()
        user_id = cursor.lastrowid
    else:
        user_id = user['id']

    # Resolver ubicación si hay coordenadas
    ubicacion_resuelta = geocodificar_coordenadas(data.latitud, data.longitud) if data.latitud and data.longitud else data.ubicacion_textual

    # Enriquecer con OpenAI
    enriquecido = enriquecer_metadata_con_openai(data.texto, ubicacion_resuelta)

    # Generar embedding
    response = openai_client.embeddings.create(
        input=data.texto,
        model="text-embedding-3-small"
    )
    embedding = response.data[0].embedding

    # Generar ID único
    pinecone_id = f"nota_{user_id}_{int(now.timestamp())}"

    # Metadata para Pinecone
    metadata = {
        "user_id": str(user_id),
        "fecha": str(fecha),
        "hora": str(hora),
        "emocion": enriquecido["emocion"],
        "categoria": enriquecido["categoria"],
        "tags": enriquecido["tags"],
        "titulo": enriquecido["titulo"],
        "resumen": enriquecido["resumen"],
        "ubicacion": ubicacion_resuelta,
        "modelo_embedding": "text-embedding-3-small"
    }
    if data.latitud is not None:
        metadata["latitud"] = data.latitud
    if data.longitud is not None:
        metadata["longitud"] = data.longitud

    # Subir a Pinecone
    index.upsert([(pinecone_id, embedding, metadata)])

    # Guardar en MySQL
    cursor.execute("""
        INSERT INTO notas (
            user_id, texto, emocion, tags, categoria,
            ubicacion_textual, latitud, longitud,
            fecha, hora, pinecone_id, resumen
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        user_id, data.texto, enriquecido["emocion"], json.dumps(enriquecido["tags"]),
        enriquecido["categoria"], ubicacion_resuelta, data.latitud, data.longitud,
        fecha, hora, pinecone_id, enriquecido["resumen"]
    ))
    db.commit()
    cursor.close()
    db.close()

    return {"status": "ok", "pinecone_id": pinecone_id}


@app.get("/notas-por-email")
def notas_por_email(email: str = Query(...)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
    user = cursor.fetchone()
    if not user:
        cursor.close()
        db.close()
        return {"notas": []}
    user_id = user['id']
    cursor.execute("SELECT * FROM notas WHERE user_id = %s ORDER BY fecha DESC, hora DESC", (user_id,))
    notas = cursor.fetchall()
    cursor.close()
    db.close()
    return {"notas": notas}


def deducir_top_k_desde_pregunta(pregunta: str) -> int:
    pregunta_lower = pregunta.lower()

    # Preguntas amplias que necesitan más contexto
    if any(p in pregunta_lower for p in ["mes", "semana", "últimos días", "resumen", "todo", "qué hice", "durante este"]):
        return 30

    # Preguntas muy concretas
    if any(p in pregunta_lower for p in ["hoy", "ayer", "quién", "dónde", "cuándo", "mi amigo", "mi mamá", "este lugar"]):
        return 5

    # Por longitud
    if len(pregunta) < 30:
        return 5
    elif len(pregunta) > 100:
        return 30

    return 15  # default



from datetime import datetime, timedelta, time, date

def convertir_fecha_hora(nota, offset):
    try:
        fecha = nota['fecha']
        hora = nota['hora']

        # Si la hora es un número (como 70626.0), convertir a horas:minutos:segundos
        if isinstance(hora, (int, float)):
            segundos = int(hora)
            hora = time(hour=segundos // 3600, minute=(segundos % 3600) // 60, second=segundos % 60)

        # Si es timedelta, también convertir
        if isinstance(hora, timedelta):
            segundos = int(hora.total_seconds())
            hora = time(hour=segundos // 3600, minute=(segundos % 3600) // 60, second=segundos % 60)

        # Parse fecha si viene como string
        if isinstance(fecha, str):
            fecha = datetime.strptime(fecha, "%Y-%m-%d").date()

        dt = datetime.combine(fecha, hora)
        return (dt + timedelta(hours=offset)).strftime("%d/%m/%Y %H:%M")

    except Exception as e:
        print(f"⚠️ Error al convertir nota ID {nota.get('id')} → {e}")
        return "(fecha inválida)"


@app.get("/buscar-notas")
def buscar_notas(email: str = Query(...), texto: str = Query(...), offset: float = Query(-3.0)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
    user = cursor.fetchone()
    if not user:
        cursor.close()
        db.close()
        return {"resultados": [], "resumen": "No se encontró el usuario."}

    user_id = user['id']
    k = deducir_top_k_desde_pregunta(texto)

    response = openai_client.embeddings.create(
        input=texto,
        model="text-embedding-3-small"
    )
    embedding = response.data[0].embedding
    resultados = index.query(
        vector=embedding,
        top_k=k,
        include_metadata=True,
        filter={"user_id": str(user_id)}
    )
    ids = [match['id'] for match in resultados.matches]
    if not ids:
        return {"resultados": [], "resumen": "No se encontraron notas relevantes."}

    placeholders = ','.join(['%s'] * len(ids))
    cursor.execute(f"SELECT * FROM notas WHERE pinecone_id IN ({placeholders})", tuple(ids))
    notas = cursor.fetchall()

    texto_notas = "\n\n".join([
        f"- {convertir_fecha_hora(n, offset)}"
        + (f" [{n['emocion']}]" if n.get('emocion') else "")
        + f": {n['texto']}"
        for n in notas
    ])

    fecha_actual = (datetime.utcnow() + timedelta(hours=offset)).strftime("%Y-%m-%d")

    prompt = f"""
Fecha actual: {fecha_actual}. Si la pregunta hace referencia a un día (como "hoy", "ayer", "anteayer"), tomá esta fecha como referencia.

Tenés la siguiente lista de notas tomadas por un usuario. Cada nota tiene fecha, hora, texto, emoción, etc.

Notas:

{texto_notas}

Pregunta: {texto}

Respondé en un tono conversacional, como si fueras un asistente personal que conoce bien a quien escribe estas notas.

Si la pregunta es concreta, respondé en una o dos frases con la mejor respuesta directa posible, basada exclusivamente en el contenido de las notas anteriores.

Si la pregunta se refiere a un estado emocional o personal actual (por ejemplo: "¿estoy contento ahora?", "¿me sentía bien hoy?", etc.), seguí estas reglas:
- Si hay una nota con emoción compatible en las últimas 12 horas, asumí que ese es su estado actual.
- Si no hay notas recientes, pero hay una nota anterior que refleja un estado emocional claro, podés mencionarla como referencia. Por ejemplo: "No hay notas recientes, pero en la última nota dijiste que estabas contento."

Si se puede inferir una persona, un lugar o una acción concreta, respondé de forma clara y directa.

Si la pregunta es genérica o busca consejos, respondé con una respuesta más amplia, pero siempre basada en las notas.
"""

    chat_response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Sos un asistente reflexivo y empático que ayuda a interpretar notas personales."},
            {"role": "user", "content": prompt}
        ]
    )
    resumen = chat_response.choices[0].message.content.strip()

    ahora = datetime.now()
    cursor.execute("""
        INSERT INTO consultas (user_id, pregunta, respuesta, fecha, hora)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        user_id,
        texto,
        resumen,
        ahora.date(),
        ahora.time()
    ))
    db.commit()

    cursor.close()
    db.close()

    return {"resultados": notas, "resumen": resumen}

app.include_router(mapa_router)
