import requests
import os

# Ahora el token viene del entorno (Render)
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN", "")

def send_message_whatsapp(to, message):
    """
    Envía un mensaje de texto por WhatsApp usando la API de Meta
    """
    url = "https://graph.facebook.com/v19.0/372901305894182/messages"  # Tu ID de WhatsApp Business
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    body = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }

    response = requests.post(url, headers=headers, json=body)
    print(f"➡️ Enviando mensaje a {to}: {message}")
    print("Respuesta de Meta:", response.status_code, response.text)
    return response.status_code
