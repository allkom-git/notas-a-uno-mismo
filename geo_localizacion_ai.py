import requests
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def geocodificar_coordenadas(lat: float, lon: float) -> str:
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={lat}&lon={lon}"
        headers = {"User-Agent": "NotasApp/1.0"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data.get("display_name", "Ubicación desconocida")
        else:
            return "Ubicación desconocida"
    except Exception as e:
        print(f"Error geocodificando: {e}")
        return "Ubicación desconocida"

def enriquecer_metadata_con_openai(texto: str, ubicacion: str = None):
    """
    Enriquece el texto con metadata y devuelve también los tokens usados
    """
    prompt = f"""Dado el siguiente texto:

{texto}

Ubicación aproximada: {ubicacion or 'No disponible'}

1. ¿Qué emoción transmite el texto? (1 palabra, por ejemplo: Feliz, Triste)
2. ¿Qué categoría podría tener este texto? (ej: Trabajo, Salud, Reflexión, Personal)
3. Lista de 1 a 5 tags relevantes, separados por coma.
4. Sugerí un título breve de hasta 5 palabras.
5. Generá un resumen breve de una frase.

Respondé cada punto en una línea distinta con este formato:
Emoción: ...
Categoría: ...
Tags: ...
Título: ...
Resumen: ...
"""
    
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    
    lines = completion.choices[0].message.content.strip().split("\n")
    result = {
        "emocion": None,
        "categoria": None,
        "tags": [],
        "titulo": None,
        "resumen": None,
        "tokens_usados": completion.usage.total_tokens  # 📊 Agregar tokens
    }

    for line in lines:
        if "Emoción" in line:
            result["emocion"] = line.split(":")[-1].strip()
        elif "Categoría" in line:
            result["categoria"] = line.split(":")[-1].strip()
        elif "Tags" in line:
            result["tags"] = [t.strip() for t in line.split(":")[-1].split(",")]
        elif "Título" in line:
            result["titulo"] = line.split(":")[-1].strip()
        elif "Resumen" in line:
            result["resumen"] = line.split(":")[-1].strip()
    
    return result