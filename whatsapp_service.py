import requests
import os

WHATSAPP_API_URL = "https://graph.facebook.com/v20.0/{}/messages".format(
    os.getenv("WHATSAPP_PHONE_ID")
)

# CORRECCIÓN IMPORTANTE: usar el nombre correcto
WHATSAPP_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")


def _post(payload):
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    return requests.post(WHATSAPP_API_URL, headers=headers, json=payload)


# ==========================================
# ENVIAR TEXTO NORMAL
# ==========================================
def send_whatsapp_text(number, message):
    payload = {
        "messaging_product": "whatsapp",
        "to": number,
        "type": "text",
        "text": {"body": message}
    }
    return _post(payload)


# ==========================================
# ENVIAR LIST MESSAGE
# ==========================================
def send_whatsapp_list(number, header, body, sections):
    payload = {
        "messaging_product": "whatsapp",
        "to": number,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": header},
            "body": {"text": body},
            "action": {
                "sections": sections,
                "button": "Seleccionar"
            }
        }
    }
    return _post(payload)


# ==========================================
# ENVIAR BOTONES
# ==========================================
def send_whatsapp_buttons(number, header, body, buttons):
    payload = {
        "messaging_product": "whatsapp",
        "to": number,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "header": {"type": "text", "text": header},
            "body": {"text": body},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": btn} for btn in buttons
                ]
            }
        }
    }
    return _post(payload)
