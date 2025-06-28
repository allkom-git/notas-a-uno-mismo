import requests
import os

# Usá el token que te dio BotFather
TOKEN = "7879332872:AAGsP2g5s1t3gxDDKnda-dXWZFhDKLD2K4A"
url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"

res = requests.get(url)
print(res.json())
