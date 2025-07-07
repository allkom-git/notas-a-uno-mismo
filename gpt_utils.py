from openai import OpenAI
import os
from dotenv import load_dotenv
from utils.db import get_db_connection
from config_openai import MODEL_CHAT_DEFAULT

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def registrar_uso_openai(user_id, modelo, tipo_consulta, prompt, usage):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("""
    INSERT INTO uso_openai (user_id, modelo, tipo_consulta, prompt, prompt_tokens, completion_tokens, total_tokens)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        user_id,
        modelo,
        tipo_consulta,
        prompt,
        usage.prompt_tokens,
        usage.completion_tokens,
        usage.total_tokens
    ))
    db.commit()
    cursor.close()
    db.close()

def completar_campos_con_openai(texto: str, user_id: int = None):
    prompt = f"""Dado el siguiente texto:
    {texto}
    1. ¿Qué emoción transmite el texto? (1 palabra, por ejemplo: Feliz, Triste)
    2. ¿Qué categoría podría tener este texto? (ej: Trabajo, Salud, Reflexión, Personal)
    3. Lista de 1 a 5 tags relevantes, separados por coma.
    4. ¿Qué ubicación textual se deduce si hay alguna? (por ejemplo, Palermo, oficina, casa)
    """
    completion = client.chat.completions.create(
        model=MODEL_CHAT_DEFAULT,
        messages=[{"role": "user", "content": prompt}]
    )
    usage = completion.usage
    content = completion.choices[0].message.content.strip()
    lines = content.split("\n")
    emocion, categoria, tags, ubicacion = None, None, [], None
    
    if len(lines) >= 4:
        emocion = lines[0].split(":")[-1].strip()
        categoria = lines[1].split(":")[-1].strip()
        tags = [t.strip() for t in lines[2].split(":")[-1].split(",")]
        ubicacion = lines[3].split(":")[-1].strip()

    if user_id:
        registrar_uso_openai(user_id, MODEL_CHAT_DEFAULT, "completar_campos", prompt, usage)

    return {
        "emocion": emocion,
        "categoria": categoria,
        "tags": tags,
        "ubicacion": ubicacion,
        "tokens": {
            "prompt": usage.prompt_tokens,
            "completion": usage.completion_tokens,
            "total": usage.total_tokens
        }
    }

def deducir_ubicacion_textual_desde_coordenadas(lat: float, lon: float):
    prompt = f"""Estas son unas coordenadas de latitud y longitud: {lat}, {lon}
¿Qué ubicación textual podrías deducir? Respondé solo el nombre del lugar (ej: Palermo, CABA o Montreal, Canadá).
"""
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return completion.choices[0].message.content.strip()