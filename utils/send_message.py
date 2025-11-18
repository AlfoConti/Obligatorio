import requests
import json
import os

TOKEN = os.getenv("WHATSAPP_TOKEN")
API_URL = os.getenv("WHATSAPP_URL")

def send_text_message(number, text):
    data = {
        "messaging_product": "whatsapp",
        "to": number,
        "type": "text",
        "text": {"body": text}
    }
    return _send(data)

def send_button_message(number, text, buttons):
    """
    buttons = [
        {"id": "buy", "title": "Comprar"},
        {"id": "menu", "title": "Ver menú"},
    ]
    """
    data = {
        "messaging_product": "whatsapp",
        "to": number,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": text},
            "action": {"buttons": [
                {"type": "reply", "reply": b} for b in buttons
            ]}
        }
    }
    return _send(data)

def send_list_message(number, header, body, sections):
    """
    sections=[
        {
            "title": "Página 1",
            "rows": [
                {"id": "P1-1", "title": "Hamburguesa"},
                {"id": "P1-2", "title": "Pizza"},
            ]
        }
    ]
    """
    data = {
        "messaging_product": "whatsapp",
        "to": number,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": header},
            "body": {"text": body},
            "action": {"sections": sections}
        }
    }
    return _send(data)

def _send(data):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TOKEN}",
    }
    response = requests.post(API_URL, headers=headers, data=json.dumps(data))
    return response.json()
