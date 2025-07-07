
from fastapi import APIRouter, Query
from utils.db import get_db_connection
from datetime import datetime

router = APIRouter()

@router.get("/uso-openai")
def obtener_uso_openai(user_email: str = Query(...), desde: str = None, hasta: str = None):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT id FROM usuarios WHERE email = %s", (user_email,))
    user = cursor.fetchone()
    if not user:
        return {"error": "Usuario no encontrado"}

    filtros = ["user_id = %s"]
    valores = [user["id"]]

    if desde:
        filtros.append("fecha >= %s")
        valores.append(desde)
    if hasta:
        filtros.append("fecha <= %s")
        valores.append(hasta)

    query = f"""
        SELECT modelo, tipo_consulta, COUNT(*) AS cantidad, 
               SUM(prompt_tokens) AS prompt_tokens,
               SUM(completion_tokens) AS completion_tokens,
               SUM(total_tokens) AS total_tokens
        FROM uso_openai
        WHERE {' AND '.join(filtros)}
        GROUP BY modelo, tipo_consulta
        ORDER BY total_tokens DESC
    """
    cursor.execute(query, valores)
    resultados = cursor.fetchall()
    cursor.close()
    db.close()
    return {"usuario": user_email, "desde": desde, "hasta": hasta, "uso": resultados}
