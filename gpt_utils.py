
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def completar_campos_con_openai(texto: str):
    prompt = f"""Dado el siguiente texto:
{texto}
1. ¿Qué emoción transmite el texto? (1 palabra, por ejemplo: Feliz, Triste)
2. ¿Qué categoría podría tener este texto? (ej: Trabajo, Salud, Reflexión, Personal)
3. Lista de 1 a 5 tags relevantes, separados por coma.
4. ¿Qué ubicación textual se deduce si hay alguna? (por ejemplo, Palermo, oficina, casa)
"""
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )

    lines = completion.choices[0].message.content.strip().split("\n")
    if len(lines) >= 4:
        emocion = lines[0].split(":")[-1].strip()
        categoria = lines[1].split(":")[-1].strip()
        tags = [t.strip() for t in lines[2].split(":")[-1].split(",")]
        ubicacion = lines[3].split(":")[-1].strip()
        return emocion, categoria, tags, ubicacion
    return None, None, [], None

def deducir_ubicacion_textual_desde_coordenadas(lat: float, lon: float):
    prompt = f"""Estas son unas coordenadas de latitud y longitud: {lat}, {lon}
¿Qué ubicación textual podrías deducir? Respondé solo el nombre del lugar (ej: Palermo, CABA o Montreal, Canadá).
"""
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return completion.choices[0].message.content.strip()
