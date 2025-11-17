# utils/send_message.py
import os
import requests
import json

# Token que pediste que esté presente (si querés usar env vars, reemplaza aquí).
ACCESS_TOKEN = "EAALZCWMF3l0cBP4ZBZCUAZBaHpco2fgDuX76oZCKiEmTFjROjRuV0ZB8rVPkFq9hWkOYgrTzZAr4vx5nQXiDq0YyVt6JrF7qiC6wxFiTHrZB8MF6NpVyFKZC99N1i2w2zZAtYpu6QNxv8lTGTDzDFnZBZC9ZAHZAzB22lgSP4c7omSsNUwYiqN1G6YbMDyAZArSxZAYFgQZDZD"
# Cambiá por el ID de tu número (o usa variable de entorno PHONE_NUMBER_ID)
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID", "846928765173274")
GRAPH_VERSION = os.environ.get("GRAPH_VERSION", "v19.0")

BASE_URL = f"https://graph.facebook.com/{GRAPH_VERSION}/{PHONE_NUMBER_ID}/messages"

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

def send_whatsapp_message(to, message_text):
    """
    Envía texto simple.
    'to' debe ser el número en formato internacional sin '+' (ej: 59891234567)
    """
    body = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message_text}
    }
    try:
        r = requests.post(BASE_URL, headers=HEADERS, json=body, timeout=10)
        print("send_whatsapp_message:", r.status_code, r.text)
        return r.status_code, r.text
    except Exception as e:
        print("Error al enviar mensaje:", e)
        return None, str(e)

# retrocompatibilidad con el nombre que usa main
def send_whatsapp_message_wrapper(to, message_text):
    return send_whatsapp_message(to, message_text)

# Export simple name used in main: send_whatsapp_message
send_whatsapp_message = send_whatsapp_message
