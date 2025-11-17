import os
import requests

WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")

API_URL = (
    f"https://graph.facebook.com/v20.0/{WHATSAPP_PHONE_ID}/messages"
    if WHATSAPP_PHONE_ID
    else None
)


def send_whatsapp_message(to_number: str, message: str, buttons=None):
    """
    Envía mensajes de texto o mensajes interactivos (botones).
    Si no hay credenciales configuradas, solo imprime un warning.
    """

    if not WHATSAPP_PHONE_ID or not WHATSAPP_ACCESS_TOKEN:
        print("\n⚠ ADVERTENCIA: No se enviará mensaje porque faltan variables de entorno.")
        print("Mensaje que NO se envió:")
        print("Para:", to_number)
        print("Texto:", message)
        if buttons:
            print("Botones:", buttons)
        return

    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    # ==============================
    #   CON BOTONES (INTERACTIVE)
    # ==============================
    if buttons:
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": message},
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

    # ==============================
    #     SOLO TEXTO
    # ==============================
    else:
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "text",
            "text": {"body": message}
        }

    response = requests.post(API_URL, headers=headers, json=payload)

    try:
        data = response.json()
    except Exception:
        data = {"error": "Respuesta no válida"}

    print("\n=== WHATSAPP API RESPONSE ===")
    print(data)

    return data
