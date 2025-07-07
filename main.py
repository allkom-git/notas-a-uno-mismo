from fastapi import FastAPI, Query
from pydantic import BaseModel
from datetime import datetime, time, timedelta, date
import os
from dotenv import load_dotenv
from pinecone import Pinecone
from openai import OpenAI
import json
from utils.db import get_db_connection
from fastapi.middleware.cors import CORSMiddleware
from gpt_utils import completar_campos_con_openai, deducir_ubicacion_textual_desde_coordenadas
from mapa import router as mapa_router
from geo_localizacion_ai import geocodificar_coordenadas, enriquecer_metadata_con_openai
from deducir_filtros_con_gpt import analizar_intencion_con_gpt
import re

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))

app = FastAPI()

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
    fecha_manual: str = None
    hora_manual: str = None


def detectar_filtros_temporales(texto: str, offset_horas: float = -3.0) -> dict:
    """
    Detecta referencias temporales en el texto y devuelve filtros de fecha
    Ajusta por timezone del usuario
    """
    texto_lower = texto.lower()
    
    # Fecha actual ajustada por timezone del usuario
    ahora_utc = datetime.utcnow()
    ahora_local = ahora_utc + timedelta(hours=offset_horas)
    hoy_local = ahora_local.date()
    
    filtros = {}
    
    if "hoy" in texto_lower:
        # Solo notas de hoy (en timezone local)
        filtros["fecha"] = {"$eq": str(hoy_local)}
        
    elif "ayer" in texto_lower:
        # Solo notas de ayer
        ayer = hoy_local - timedelta(days=1)
        filtros["fecha"] = {"$eq": str(ayer)}
        
    elif any(palabra in texto_lower for palabra in ["esta semana", "semana", "últimos 7 días", "últimos días"]):
        # Últimos 7 días
        hace_7_dias = hoy_local - timedelta(days=7)
        filtros["fecha"] = {"$gte": str(hace_7_dias), "$lte": str(hoy_local)}
        
    elif "este mes" in texto_lower:
        # Este mes
        inicio_mes = hoy_local.replace(day=1)
        filtros["fecha"] = {"$gte": str(inicio_mes), "$lte": str(hoy_local)}
        
    elif any(palabra in texto_lower for palabra in ["últimos 30 días", "último mes"]):
        # Últimos 30 días
        hace_30_dias = hoy_local - timedelta(days=30)
        filtros["fecha"] = {"$gte": str(hace_30_dias), "$lte": str(hoy_local)}
    
    # Detectar fechas específicas como "5 de julio"
    match_dia_mes = re.search(r"(\d{1,2}) de (enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)", texto_lower)
    if match_dia_mes:
        dia = int(match_dia_mes.group(1))
        mes_nombres = {
            "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
            "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
        }
        mes = mes_nombres.get(match_dia_mes.group(2), 7)  # Default julio
        try:
            fecha_especifica = date(2025, mes, dia)
            filtros["fecha"] = {"$eq": str(fecha_especifica)}
        except ValueError:
            pass  # Fecha inválida, ignorar
    
    return filtros


@app.post("/guardar-nota")
def guardar_nota(data: NotaRequest):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    # 📊 Contador de tokens
    tokens_usados = {
        "embedding": 0,
        "enriquecimiento": 0,
        "total": 0
    }

    now = datetime.utcnow()  # ⚠️ Usar UTC para consistencia
    try:
        if data.fecha_manual:
            dt = datetime.fromisoformat(data.fecha_manual)
            # Convertir a UTC si viene con timezone local
            fecha = dt.date()
            hora = dt.time()
        else:
            fecha = now.date()
            hora = now.time()

        if data.hora_manual:
            hora = datetime.strptime(data.hora_manual, "%H:%M").time()

    except ValueError:
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

    # 🧠 Enriquecimiento con IA
    ubicacion_resuelta = geocodificar_coordenadas(data.latitud, data.longitud) if data.latitud and data.longitud else data.ubicacion_textual
    
    enriquecido = enriquecer_metadata_con_openai(data.texto, ubicacion_resuelta)
    tokens_usados["enriquecimiento"] = enriquecido.get("tokens_usados", 0)

    # 🔤 Crear embedding
    response = openai_client.embeddings.create(
        input=data.texto,
        model="text-embedding-3-small"
    )
    embedding = response.data[0].embedding
    tokens_usados["embedding"] = response.usage.total_tokens
    tokens_usados["total"] = tokens_usados["embedding"] + tokens_usados["enriquecimiento"]

    pinecone_id = f"nota_{user_id}_{int(datetime.now().timestamp())}"

    metadata = {
        "user_id": str(user_id),
        "fecha": str(fecha),  # Guardar como string YYYY-MM-DD
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

    index.upsert([(pinecone_id, embedding, metadata)])

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

    return {
        "status": "ok", 
        "pinecone_id": pinecone_id,
        "tokens_usados": tokens_usados
    }


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

    if not notas:
        return {"resultados": [], "resumen": "No se encontraron notas que coincidan con los filtros."}

    cursor.close()
    db.close()
    return {"notas": notas}


def convertir_fecha_hora(nota, offset):
    """
    Convierte fecha y hora de una nota para mostrar en timezone local
    """
    try:
        fecha = nota['fecha']
        hora = nota['hora']
        
        # Convertir fecha de string a date object si es necesario
        if isinstance(fecha, str):
            fecha = datetime.strptime(fecha, "%Y-%m-%d").date()
        
        # Convertir hora según el tipo que venga
        if isinstance(hora, str):
            # Si viene como string "HH:MM:SS"
            if ":" in hora:
                hora = datetime.strptime(hora, "%H:%M:%S").time()
            else:
                # Si viene como string de segundos
                segundos = int(float(hora))
                hora = time(hour=segundos // 3600, minute=(segundos % 3600) // 60, second=segundos % 60)
        elif isinstance(hora, (int, float)):
            # Si viene como número de segundos
            segundos = int(hora)
            hora = time(hour=segundos // 3600, minute=(segundos % 3600) // 60, second=segundos % 60)
        elif isinstance(hora, timedelta):
            # Si viene como timedelta
            segundos = int(hora.total_seconds())
            hora = time(hour=segundos // 3600, minute=(segundos % 3600) // 60, second=segundos % 60)
        
        # Crear datetime y convertir timezone
        dt = datetime.combine(fecha, hora)
        # No aplicar offset si ya está en la timezone correcta
        dt_formatted = dt.strftime("%d/%m/%Y %H:%M")
        
        return dt_formatted
        
    except Exception as e:
        print(f"⚠️ Error al convertir fecha/hora de nota {nota.get('pinecone_id', 'unknown')}: {e}")
        print(f"   Fecha original: {nota.get('fecha')} (tipo: {type(nota.get('fecha'))})")
        print(f"   Hora original: {nota.get('hora')} (tipo: {type(nota.get('hora'))})")
        return f"{nota.get('fecha', '????')} {nota.get('hora', '??:??')}"


@app.get("/buscar-notas")
def buscar_notas(email: str = Query(...), texto: str = Query(...), offset: float = Query(-3.0)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    # 📊 Contador de tokens para búsqueda
    tokens_usados = {
        "filtros_gpt": 0,
        "embedding_busqueda": 0,
        "resumen_final": 0,
        "total": 0
    }
    
    cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
    user = cursor.fetchone()
    if not user:
        cursor.close()
        db.close()
        return {"resultados": [], "resumen": "No se encontró el usuario.", "tokens_usados": tokens_usados}

    user_id = user['id']
    
    # 🧠 Análisis de intención con GPT
    intencion_resultado = analizar_intencion_con_gpt(texto)
    tokens_usados["filtros_gpt"] = intencion_resultado.get("tokens_usados", 0)
    
    k = intencion_resultado.get("top_k", 15)
    filtros_gpt = intencion_resultado.get("filtros", {})
    
    # 📅 Detectar filtros temporales mejorados
    filtros_temporales = detectar_filtros_temporales(texto, offset)
    
    print(f"🔍 Debug búsqueda:")
    print(f"   Pregunta: {texto}")
    print(f"   Offset usuario: {offset} horas")
    print(f"   Fecha actual UTC: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}")
    print(f"   Fecha actual local: {(datetime.utcnow() + timedelta(hours=offset)).strftime('%Y-%m-%d %H:%M')}")
    print(f"   Filtros temporales detectados: {filtros_temporales}")
    print(f"   Filtros GPT: {filtros_gpt}")

    # 🔤 Crear embedding para búsqueda semántica
    response = openai_client.embeddings.create(
        input=texto,
        model="text-embedding-3-small"
    )
    embedding = response.data[0].embedding
    tokens_usados["embedding_busqueda"] = response.usage.total_tokens

    # 🎯 Buscar en Pinecone con filtros combinados
    filtros_pinecone = {"user_id": {"$eq": str(user_id)}}
    
    # Agregar filtros temporales a Pinecone
    if filtros_temporales:
        filtros_pinecone.update(filtros_temporales)
    
    # Agregar otros filtros de GPT
    if filtros_gpt.get("emocion"):
        filtros_pinecone["emocion"] = {"$eq": filtros_gpt["emocion"]}
    if filtros_gpt.get("categoria"):
        filtros_pinecone["categoria"] = {"$eq": filtros_gpt["categoria"]}
    
    print(f"🎯 Filtros finales Pinecone: {filtros_pinecone}")

    try:
        # Búsqueda vectorial con filtros en Pinecone
        resultados_pinecone = index.query(
            vector=embedding,
            top_k=min(k * 2, 100),  # Buscar más para luego filtrar
            include_metadata=True,
            filter=filtros_pinecone
        )
        
        print(f"📊 Resultados Pinecone: {len(resultados_pinecone.matches)} notas encontradas")
        
        if not resultados_pinecone.matches:
            return {
                "resultados": [], 
                "resumen": "No se encontraron notas que coincidan con los filtros temporales y de contenido.",
                "tokens_usados": tokens_usados,
                "debug_info": {
                    "filtros_aplicados": filtros_pinecone,
                    "filtros_temporales": filtros_temporales,
                    "offset_horas": offset
                }
            }

        # 📝 Obtener textos completos desde MySQL usando pinecone_ids
        resultados = []
        if resultados_pinecone.matches:
            pinecone_ids = [match.id for match in resultados_pinecone.matches[:k]]
            
            # Buscar todas las notas de MySQL en una sola query
            placeholders = ",".join(["%s"] * len(pinecone_ids))
            cursor.execute(f"""
                SELECT pinecone_id, texto, fecha, hora, emocion, categoria, 
                       tags, ubicacion_textual, resumen, latitud, longitud
                FROM notas 
                WHERE pinecone_id IN ({placeholders}) AND user_id = %s
                ORDER BY fecha DESC, hora DESC
            """, tuple(pinecone_ids + [user_id]))
            
            # Crear diccionario para lookup rápido
            notas_mysql = {row['pinecone_id']: row for row in cursor.fetchall()}
            
            # 🔍 Debug: Ver tipos de datos que vienen de MySQL
            if notas_mysql:
                primera_nota = next(iter(notas_mysql.values()))
                print(f"🔍 Debug tipos de datos MySQL:")
                print(f"   fecha: {primera_nota['fecha']} (tipo: {type(primera_nota['fecha'])})")
                print(f"   hora: {primera_nota['hora']} (tipo: {type(primera_nota['hora'])})")
                print(f"   texto: {primera_nota['texto'][:50]}...")
            
            # Combinar datos de Pinecone (scores) con datos de MySQL (contenido)
            for match in resultados_pinecone.matches[:k]:
                pinecone_id = match.id
                mysql_data = notas_mysql.get(pinecone_id)
                
                if mysql_data:
                    # Usar datos de MySQL como fuente principal, agregar score de Pinecone
                    # El título viene de los metadatos de Pinecone, no de MySQL
                    nota = {
                        "pinecone_id": pinecone_id,
                        "texto": mysql_data['texto'],
                        "fecha": str(mysql_data['fecha']),
                        "hora": str(mysql_data['hora']),
                        "emocion": mysql_data['emocion'],
                        "categoria": mysql_data['categoria'],
                        "tags": mysql_data['tags'] if isinstance(mysql_data['tags'], list) else 
                               json.loads(mysql_data['tags']) if mysql_data['tags'] else [],
                        "titulo": match.metadata.get('titulo', mysql_data['texto'][:40] + '...' if mysql_data['texto'] else 'Sin título'),
                        "resumen": mysql_data['resumen'],
                        "ubicacion_textual": mysql_data['ubicacion_textual'],
                        "latitud": mysql_data['latitud'],
                        "longitud": mysql_data['longitud'],
                        "score": match.score  # Score semántico de Pinecone
                    }
                    resultados.append(nota)
                else:
                    print(f"⚠️ Nota {pinecone_id} encontrada en Pinecone pero no en MySQL")
            
            print(f"📊 Combinadas {len(resultados)} notas de Pinecone + MySQL")

        # 📝 Crear resumen con GPT
        texto_notas = "\n\n".join([
            f"- {convertir_fecha_hora(n, offset)}"
            + (f" [{n['emocion']}]" if n.get('emocion') else "")
            + f": {n.get('texto', n.get('resumen', ''))}"
            for n in resultados
        ])

        fecha_actual = (datetime.utcnow() + timedelta(hours=offset)).strftime("%Y-%m-%d")
        
        # 🔍 Debug: Mostrar qué se envía a GPT
        print(f"📝 Enviando a GPT:")
        print(f"   Fecha actual: {fecha_actual}")
        print(f"   Notas encontradas: {len(resultados)}")
        print(f"   Primeras 200 chars del texto_notas: {texto_notas[:200]}...")

        prompt = f"""
Fecha actual: {fecha_actual}. Si la pregunta hace referencia a un día (como "hoy", "ayer", "anteayer"), tomá esta fecha como referencia.

Tenés la siguiente lista de notas tomadas por un usuario. Cada nota tiene fecha, hora, texto, emoción, etc.

Notas encontradas ({len(resultados)} notas):

{texto_notas}

Pregunta: {texto}

Respondé en un tono conversacional, como si fueras un asistente personal que conoce bien a quien escribe estas notas.

Si la pregunta incluye múltiples temas, podés agrupar por emoción, tags o día. Si menciona "más usados" o "resumen", incluí estadísticas también.
"""

        # 🧠 Resumen final con GPT
        chat_response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Sos un asistente reflexivo y empático que ayuda a interpretar notas personales."},
                {"role": "user", "content": prompt}
            ]
        )
        resumen = chat_response.choices[0].message.content.strip()
        tokens_usados["resumen_final"] = chat_response.usage.total_tokens

    except Exception as e:
        print(f"❌ Error en búsqueda Pinecone: {e}")
        return {
            "resultados": [], 
            "resumen": f"Error en la búsqueda: {str(e)}",
            "tokens_usados": tokens_usados
        }

    # Calcular total de tokens
    tokens_usados["total"] = sum([
        tokens_usados["filtros_gpt"],
        tokens_usados["embedding_busqueda"], 
        tokens_usados["resumen_final"]
    ])

    # Guardar consulta en base de datos
    ahora = datetime.utcnow()
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

    return {
        "resultados": resultados, 
        "resumen": resumen,
        "tokens_usados": tokens_usados,
        "debug_info": {
            "notas_encontradas": len(resultados),
            "filtros_aplicados": filtros_pinecone,
            "filtros_temporales": filtros_temporales
        }
    }


app.include_router(mapa_router)