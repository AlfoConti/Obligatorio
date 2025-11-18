import requests
import json
import os

WHATSAPP_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")

def send_whatsapp_buttons(to_number):
    url = f"https://graph.facebook.com/v21.0/{WHATSAPP_PHONE_ID}/messages"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": "Bienvenido 👋\nSelecciona una opción:"
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": "menu_productos",
                            "title": "📦 Ver Productos"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "ver_carrito",
                            "title": "🛒 Ver Carrito"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "ayuda",
                            "title": "❓ Ayuda"
                        }
                    }
                ]
            }
        }
    }

    response = requests.post(url, headers=headers, json=data)
    print("BOTONES RESPUESTA:", response.text)
    return response


def send_whatsapp_text(number, text):
    url = f"https://graph.facebook.com/v21.0/{WHATSAPP_PHONE_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "messaging_product": "whatsapp",
        "to": number,
        "type": "text",
        "text": { "body": text }
    }

    response = requests.post(url, headers=headers, json=data)
    print("TEXTO RESPUESTA:", response.text)
    return response
