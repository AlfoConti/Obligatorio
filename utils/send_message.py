# utils/send_message.py
import os
import json
import requests
import logging

logger = logging.getLogger("uvicorn.error")

WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")

def send_whatsapp_message(to_number: str, message_text: str):
    """
    Envía un mensaje de texto simple via WhatsApp Cloud API.
    Si faltan las variables de entorno, NO corta la app.
    Simplemente devuelve un error controlado.
    """
    if not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_PHONE_ID:
        err = "WhatsApp env vars missing. Message not sent."
        logger.error(err)
        return {"error": err}

    url = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": message_text}
    }

    try:
        r = requests.post(url, headers=headers, data=json.dumps(payload))
        return r.json()
    except Exception as e:
        logger.exception("Error sending WhatsApp message")
        return {"error": str(e)}
