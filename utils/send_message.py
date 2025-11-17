import requests
import json

TOKEN = "TU_TOKEN_DE_WHATSAPP"
PHONE_ID = "TU_PHONE_NUMBER_ID"

def send_text(to, text):
    url = f"https://graph.facebook.com/v19.0/{PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }

    return requests.post(url, headers=headers, data=json.dumps(data)).json()


def send_interactive_button(to, body, button_title, button_id):
    url = f"https://graph.facebook.com/v19.0/{PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body},
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": button_id,
                            "title": button_title
                        }
                    }
                ]
            }
        }
    }

    return requests.post(url, headers=headers, data=json.dumps(data)).json()


def send_interactive_list(to, title, body, sections):
    url = f"https://graph.facebook.com/v19.0/{PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {"text": body},
            "header": {"type": "text", "text": title},
            "footer": {"text": "Selecciona una opción"},
            "action": {
                "button": "Ver opciones",
                "sections": sections
            }
        }
    }

    return requests.post(url, headers=headers, data=json.dumps(data)).json()
