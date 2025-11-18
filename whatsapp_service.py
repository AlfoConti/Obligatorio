import requests
import os

WHATSAPP_API_URL = f"https://graph.facebook.com/v20.0/{os.getenv('WHATSAPP_PHONE_ID')}/messages"
WHATSAPP_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")


def _post(payload):
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    return requests.post(WHATSAPP_API_URL, headers=headers, json=payload)


# ==========================================
# ENVIAR TEXTO
# ==========================================
def send_whatsapp_text(number, message):
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number,
        "type": "text",
        "text": {
            "body": message
        }
    }
    return _post(payload)


# ==========================================
# ENVIAR LIST MESSAGE
# ==========================================
def send_whatsapp_list(number, header, body, sections):
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": header},
            "body": {"text": body},
            "action": {
                "button": "Seleccionar",
                "sections": sections
            }
        }
    }
    return _post(payload)


# ==========================================
# ENVIAR BOTONES — CORRECTO PARA 2025
# ==========================================
def send_whatsapp_buttons(number, header, body, buttons):
    """
    buttons debe ser una lista:
    [
        {"id": "btn_catalogo", "title": "Ver catálogo"},
        {"id": "btn_carrito", "title": "Ver carrito"}
    ]
    """
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "header": {
                "type": "text",
                "text": header
            },
            "body": {
                "text": body
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": btn["id"],
                            "title": btn["title"]
                        }
                    }
                    for btn in buttons
                ]
            }
        }
    }

    return _post(payload)
