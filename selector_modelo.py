### selector_modelo.py
# Módulo para seleccionar automáticamente el modelo OpenAI más conveniente
# según tipo de tarea, sensibilidad, cantidad de tokens y costo estimado.

# Precios actualizados a julio 2025:
# gpt-3.5-turbo: $0.0005 (input), $0.0015 (output) por 1K tokens
# gpt-4o: $0.005 (input), $0.015 (output) por 1K tokens

def seleccionar_modelo_y_costo(tarea: str, tokens_estimados: int, sensibilidad: str = "media") -> dict:
    """
    Selecciona el modelo más adecuado y estima el costo en USD.

    Parámetros:
    - tarea: 'extraccion', 'clasificacion', 'resumen', 'respuesta'
    - tokens_estimados: tokens totales (entrada + salida)
    - sensibilidad: 'baja', 'media', 'alta'

    Retorna un diccionario con:
    - modelo sugerido
    - costo estimado en USD
    - tokens usados
    """

    tarea = tarea.lower()
    sensibilidad = sensibilidad.lower()

    if tokens_estimados > 16000:
        return {
            "modelo": "⚠️ Excede el límite de gpt-4o (16K). Dividir input.",
            "costo_estimado_usd": None,
            "tokens": tokens_estimados
        }

    # Reglas de selección del modelo
    if tarea in ["extraccion", "clasificacion"] and sensibilidad == "baja":
        modelo = "gpt-3.5-turbo"
    elif tarea == "resumen":
        modelo = "gpt-4o" if sensibilidad == "alta" or tokens_estimados > 8000 else "gpt-3.5-turbo"
    elif tarea == "respuesta":
        modelo = "gpt-4o" if sensibilidad == "alta" or tokens_estimados > 6000 else "gpt-3.5-turbo"
    else:
        modelo = "gpt-4o"

    # Precios por mil tokens
    precios = {
        "gpt-3.5-turbo": {"in": 0.0005, "out": 0.0015},
        "gpt-4o": {"in": 0.005, "out": 0.015}
    }

    tokens_in = tokens_out = tokens_estimados / 2
    precio_in = precios[modelo]["in"]
    precio_out = precios[modelo]["out"]
    costo = (tokens_in / 1000) * precio_in + (tokens_out / 1000) * precio_out

    return {
        "modelo": modelo,
        "costo_estimado_usd": round(costo, 6),
        "tokens": tokens_estimados
    }

# Ejemplo de uso directo
if __name__ == "__main__":
    ejemplo = seleccionar_modelo_y_costo("respuesta", 7000, "alta")
    print(ejemplo)
