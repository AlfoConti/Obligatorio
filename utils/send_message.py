import os
import requests
import json

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")
API_VERSION = os.getenv("WHATSAPP_API_VERSION", "v21.0")

# Construimos automáticamente la URL
WHATSAPP_API_URL = f"https://graph.facebook.com/{API_VERSION}/{PHONE_ID}/messages"


def send_message(payload: dict):
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    print("Sending to:", WHATSAPP_API_URL)
    print("Payload:", payload)

    response = requests.post(WHATSAPP_API_URL, headers=headers, data=json.dumps(payload))
    print("Response:", response.text)
    return response


def send_text_message(to: str, text: str):
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }
    return send_message(payload)


def send_button_message(to: str, body: str, buttons: list):
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body},
            "action": {"buttons": [
                {
                    "type": "reply",
                    "reply": {"id": b["id"], "title": b["title"]}
                } for b in buttons
            ]}
        }
    }
    return send_message(payload)


def send_list_message(to: str, header: str, body: str, sections: list):
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": header},
            "body": {"text": body},
            "action": {
                "sections": sections,
                "button": "Ver opciones"
            }
        }
    }
    return send_message(payload)
