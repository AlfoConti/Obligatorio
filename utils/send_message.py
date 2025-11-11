import requests

# 👉 Token de acceso largo de Meta
ACCESS_TOKEN = "EAALZCWMF3l0cBP3inTc96o4MrG2Sq8ExIN7WblqBqFXpdS1Cv9D7Fr7rhijNZCSIIZCREXF8PS40BhTCZA49XyjSoCLhn6PA9G9UKS4cGj5TZCZCVjVIBK8RDqNZCJuNz6Kapnzi79ef9m828YVoYeVBtLcBkIT3YzZCEoYaw15WCD6F6ZC9ysrbZCgJXeEgHnCgZDZD"

def send_whatsapp_message(to, message):
    """
    Envía un mensaje de texto por WhatsApp usando la API de Meta
    """
    url = "https://graph.facebook.com/v19.0/372901305894182/messages"  # Cambiá el número por el ID de tu WhatsApp Business
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
