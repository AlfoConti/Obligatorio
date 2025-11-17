import requests
import os
import json

# Token y número del business
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

API_URL = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"


def send_request(payload):
    """Enviar el mensaje genérico a la API de WhatsApp."""
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }

    response = requests.post(API_URL, headers=headers, data=json.dumps(payload))

    print("WhatsApp API response:", response.text)
    return response.json()


# ──────────────────────────────────────────────────────
# MENSAJES DE TEXTO
# ──────────────────────────────────────────────────────
def send_text_message(to, message):
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message},
    }
    return send_request(payload)


# ──────────────────────────────────────────────────────
# MENSAJES CON BOTONES
# ──────────────────────────────────────────────────────
def send_button_message(to, body, buttons):
    """
    buttons = [
        {"id": "ACTION1", "title": "Texto"},
        {"id": "ACTION2", "title": "Texto"}
    ]
    """
    button_objects = [
        {"type": "reply", "reply": {"id": btn["id"], "title": btn["title"]}}
        for btn in buttons
    ]

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body},
            "action": {"buttons": button_objects},
        },
    }

    return send_request(payload)


# ──────────────────────────────────────────────────────
# LISTAS (CATÁLOGO)
# ──────────────────────────────────────────────────────
def send_list_message(to, title, body, sections):
    """
    sections = [
        {
            "title": "Pizzas",
            "rows": [
                {"id": "SHOW_PRODUCT:1", "title": "Muzzarella"},
                {"id": "SHOW_PRODUCT:2", "title": "Napolitana"}
            ]
        }
    ]
    """
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": title},
            "body": {"text": body},
            "action": {"sections": sections},
        },
    }
    return send_request(payload)


# ──────────────────────────────────────────────────────
# ENVIAR UBICACIÓN
# ──────────────────────────────────────────────────────
def send_location_message(to, lat, lon, name="Ubicación", address=""):
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "location",
        "location": {
            "latitude": lat,
            "longitude": lon,
            "name": name,
            "address": address,
        },
    }
    return send_request(payload)


# ──────────────────────────────────────────────────────
# ENVIAR IMÁGENES (PARA MAPA DE RUTA)
# ──────────────────────────────────────────────────────
def send_image_message(to, image_url, caption=""):
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "image",
        "image": {"link": image_url, "caption": caption},
    }
    return send_request(payload)
