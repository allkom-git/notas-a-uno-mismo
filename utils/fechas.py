import re
from datetime import datetime, timedelta
import dateparser

def obtener_filtro_fecha(texto: str) -> dict | None:
    """
    Detecta referencias temporales en texto y devuelve un filtro compatible
    con Pinecone para el campo 'fecha'. Soporta:
    - Fechas exactas (ej. "el 24 de junio")
    - Fechas relativas (hoy, ayer, este mes, última semana)
    - Rangos (ej. "entre el 10 y el 15 de junio", "del 1 al 5 de mayo")
    """
    texto_lower = texto.lower()
    hoy = datetime.now().date()

    # 🔍 Rango entre dos fechas con expresiones comunes
    match_rango = re.search(r"(entre|del|desde)\s+(.*?)\s+(y|hasta|al)\s+(.*?)(\s|$)", texto_lower)
    if match_rango:
        desde_raw = match_rango.group(2)
        hasta_raw = match_rango.group(4)
        desde = dateparser.parse(desde_raw, settings={"PREFER_DATES_FROM": "past"})
        hasta = dateparser.parse(hasta_raw, settings={"PREFER_DATES_FROM": "past"})
        if desde and hasta:
            desde_fecha = desde.date().isoformat()
            hasta_fecha = hasta.date().isoformat()
            return {"fecha": {"$gte": desde_fecha, "$lte": hasta_fecha}}

    # 📅 Fechas relativas simples
    if "hoy" in texto_lower:
        return {"fecha": hoy.isoformat()}
    elif "ayer" in texto_lower:
        return {"fecha": (hoy - timedelta(days=1)).isoformat()}
#    elif "última semana" in texto_lower or "últimos 7 días" in texto_lower:
#        return {
#            "fecha": {
#                "$gte": (hoy - timedelta(days=7)).isoformat(),
#                "$lte": hoy.isoformat()
#            }
#        }
#    elif "últimos días" in texto_lower or "últimos 3 días" in texto_lower:
#        return {
#            "fecha": {
#                "$gte": (hoy - timedelta(days=3)).isoformat(),
#                "$lte": hoy.isoformat()
#            }
#        }
#    elif "este mes" in texto_lower:
#        comienzo_mes = hoy.replace(day=1)
#        return {
#            "fecha": {
#                "$gte": comienzo_mes.isoformat(),
#                "$lte": hoy.isoformat()
#            }
#        }

    # 📆 Fecha única
    fecha_detectada = dateparser.parse(texto, settings={"PREFER_DATES_FROM": "past"})
    if fecha_detectada:
        return {"fecha": fecha_detectada.date().isoformat()}

    return None
