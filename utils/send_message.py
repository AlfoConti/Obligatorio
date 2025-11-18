# utils/send_message.py
import os
import requests
import json

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")
WHATSAPP_API_VERSION = os.getenv("WHATSAPP_API_VERSION", "v21.0")

# Construimos la URL si PHONE_ID está presente; si no, será None (debug)
WHATSAPP_API_URL = None
if WHATSAPP_PHONE_ID:
    WHATSAPP_API_URL = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}/{WHATSAPP_PHONE_ID}/messages"

def _post(payload):
    if not WHATSAPP_API_URL or not WHATSAPP_TOKEN:
        print("WARNING: WHATSAPP_API_URL or WHATSAPP_TOKEN not configured.")
        print("WHATSAPP_API_URL:", WHATSAPP_API_URL)
        print("WHATSAPP_TOKEN:", "set" if WHATSAPP_TOKEN else "NOT SET")
        return None

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    try:
        resp = requests.post(WHATSAPP_API_URL, headers=headers, data=json.dumps(payload), timeout=10)
        print("SEND ->", json.dumps(payload, ensure_ascii=False))
        print("RESP ->", resp.status_code, resp.text)
        return resp
    except Exception as e:
        print("Exception sending message:", e)
        return None

def send_text_message(to: str, body: str):
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": body}
    }
    return _post(payload)

def send_button_message(to: str, body: str, buttons: list, header: str = None):
    """
    buttons: [{"id":"btn_1","title":"Comprar"}, ...] up to 3
    """
    action_buttons = [{"type": "reply", "reply": {"id": b["id"], "title": b["title"]}} for b in buttons]
    interactive = {
        "type": "button",
        "body": {"text": body},
        "action": {"buttons": action_buttons}
    }
    if header:
        interactive["header"] = {"type": "text", "text": header}
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": interactive
    }
    return _post(payload)

def send_list_message(to: str, header: str, body: str, sections: list, button_text: str = "Ver opciones"):
    """
    sections: list of {"title": "...", "rows":[{"id":"rowid","title":"...","description": "..."}]}
    Keep total rows <= 10 (Meta rule).
    """
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": header},
            "body": {"text": body},
            "action": {
                "button": button_text,
                "sections": sections
            }
        }
    }
    return _post(payload)
