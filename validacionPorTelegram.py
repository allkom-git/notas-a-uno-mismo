from fastapi import APIRouter, HTTPException, Query, Request
import os
import requests
import random
import time
from dotenv import load_dotenv
import json
from utils.db import get_db_connection
from fastapi.middleware.cors import CORSMiddleware
from gpt_utils import completar_campos_con_openai, deducir_ubicacion_textual_desde_coordenadas

app.include_router(validacion_router)

load_dotenv()

router = APIRouter()

#TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
#TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # o buscar dinámicamente si fuera necesario

TELEGRAM_BOT_TOKEN = "7879332872:AAGsP2g5s1t3gxDDKnda-dXWZFhDKLD2K4A"
TELEGRAM_CHAT_ID = "1022175805"


# Simulador de almacenamiento temporal en memoria
# En producción esto se puede reemplazar por Redis, Memcached o SQLite temporal
codigos_temporales = {}

@router.post("/enviar-codigo")
def enviar_codigo(email: str = Query(...), telefono: str = Query(...)):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise HTTPException(status_code=500, detail="Faltan las variables de entorno para Telegram")

    codigo = random.randint(100000, 999999)
    timestamp = int(time.time())
    codigos_temporales[email] = {"codigo": str(codigo), "timestamp": timestamp}

    mensaje = f"\ud83d\udd12 Tu c\u00f3digo de acceso para {email} es: *{codigo}*\n\nCaduca en 5 minutos."
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown"
    }

    resp = requests.post(url, json=payload)
    if not resp.ok:
        raise HTTPException(status_code=500, detail="No se pudo enviar el mensaje por Telegram")

    return {"status": "ok", "mensaje": "Código enviado por Telegram", "codigo": codigo}


@router.post("/validar-codigo")
def validar_codigo(email: str = Query(...), codigo_ingresado: str = Query(...)):
    registro = codigos_temporales.get(email)
    if not registro:
        raise HTTPException(status_code=400, detail="No se encontró un código para este email")

    ahora = int(time.time())
    if ahora - registro["timestamp"] > 300:
        del codigos_temporales[email]
        raise HTTPException(status_code=400, detail="El código expiró")

    if codigo_ingresado != registro["codigo"]:
        raise HTTPException(status_code=401, detail="Código incorrecto")

    # Validado correctamente
    del codigos_temporales[email]  # Limpieza opcional
    return {"status": "validado", "mensaje": "Código correcto"}
