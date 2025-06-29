from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analizar_intencion_con_gpt(pregunta: str) -> dict:
    system_prompt = """Sos un asistente que ayuda a traducir una pregunta de un usuario sobre sus notas personales a filtros para búsqueda en una base de datos.

Dado el texto de una pregunta, devolvés un JSON con alguno de los siguientes campos si se pueden deducir:
- fecha (formato YYYY-MM-DD)
- fecha_hasta (opcional, para rango)
- emocion (ej: "Triste", "Feliz")
- categoria (ej: "Trabajo", "Salud")
- tags (lista de palabras clave)
- ubicacion (ej: "Recoleta", "Oficina")
- top_k (int, cuántas notas se deben buscar)

Solo devolvés campos si hay una inferencia clara. Si no hay nada claro, devolvé solo {"top_k": 15}.
"""

    user_prompt = f"Texto de la pregunta: {pregunta}\n\nRespondé solo con el JSON de filtros."

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        contenido = response.choices[0].message.content.strip()

        # Intentar parsear como JSON
        import json
        filtros = json.loads(contenido)
        if isinstance(filtros, dict):
            return filtros
        else:
            return {"top_k": 15}
    except Exception as e:
        print(f"Error al deducir filtros con GPT: {e}")
        return {"top_k": 15}
