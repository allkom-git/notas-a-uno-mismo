from fastapi import APIRouter, Query
from utils.db import get_db_connection

router = APIRouter()

@router.get("/mapa-notas")
def mapa_notas(email: str = Query(...)):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
    user = cursor.fetchone()
    if not user:
        cursor.close()
        db.close()
        return {"notas": []}

    user_id = user["id"]

    cursor.execute("""
        SELECT id, texto, latitud, longitud, fecha, hora
        FROM notas
        WHERE user_id = %s AND latitud IS NOT NULL AND longitud IS NOT NULL
    """, (user_id,))
    notas = cursor.fetchall()

    cursor.close()
    db.close()
    return {"notas": notas}
