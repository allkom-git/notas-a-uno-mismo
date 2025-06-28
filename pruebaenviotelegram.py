import requests

# Reemplazá con tu token real y chat_id real

TELEGRAM_BOT_TOKEN = "7879332872:AAGsP2g5s1t3gxDDKnda-dXWZFhDKLD2K4A"
TELEGRAM_CHAT_ID = "1022175805"

mensaje = "🚀 ¡Este es un mensaje de prueba desde tu backend FastAPI!"

url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
params = {
    "chat_id": TELEGRAM_CHAT_ID,
    "text": mensaje
}

response = requests.get(url, params=params)
print(response.status_code)
print(response.json())
