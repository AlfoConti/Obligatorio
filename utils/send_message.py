# utils/send_message.py
import os
import json
import requests
import logging

logger = logging.getLogger("uvicorn.error")

WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")

if not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_PHONE_ID:
    logger.warning("WHATSAPP_ACCESS_TOKEN or WHATSAPP_PHONE_ID not set in env variables. Sending will fail until set.")


def send_whatsapp_message(to_number: str, message_text: str):
    """
    Envía un mensaje de texto simple via WhatsApp Cloud API.
    Retorna la respuesta JSON (o lanza excepción si falla).
    """
    if not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_PHONE_ID:
        logger.error("Missing WhatsApp env vars (ACCESS_TOKEN or PHONE_ID).")
        raise RuntimeError("WhatsApp env vars missing")

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

    logger.info("Sending WhatsApp message to %s: %s", to_number, message_text)
    r = requests.post(url, headers=headers, data=json.dumps(payload))
    try:
        resp = r.json()
    except Exception:
        resp = {"status_code": r.status_code, "text": r.text}

    logger.info("WhatsApp API response: %s", resp)
    return resp
