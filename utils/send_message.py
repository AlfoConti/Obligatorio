import requests
import json
import os

def generate_data(text_user, number_user):
    return {
        "messaging_product": "whatsapp",
        "to": number_user,
        "type": "text",
        "text": {
            "body": text_user
        }
    }

def send_message_whatsapp(text_user, number_user):
    try:
        # Se pueden definir en Render → Environment
        token = os.environ.get("WHATSAPP_ACCESS_TOKEN", "EAALZCWMF3l0cBP3inTc96o4MrG2Sq8ExIN7WblqBqFXpdS1Cv9D7Fr7rhijNZCSIIZCREXF8PS40BhTCZA49XyjSoCLhn6PA9G9UKS4cGj5TZCZCVjVIBK8RDqNZCJuNz6Kapnzi79ef9m828YVoYeVBtLcBkIT3YzZCEoYaw15WCD6F6ZC9ysrbZCgJXeEgHnCgZDZD")
        api_url = os.environ.get("WHATSAPP_API_URL", "https://graph.facebook.com/v22.0/846928765173274/messages")

        data = generate_data(text_user, number_user)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }

        print(f"📤 Enviando mensaje a {number_user}: {text_user}")
        response = requests.post(api_url, headers=headers, json=data)

        print(f"📡 Respuesta del servidor: {response.status_code} - {response.text}")

        if response.status_code == 200:
            print("✅ Mensaje enviado correctamente a WhatsApp")
            return True
        else:
            print("⚠️ No se pudo enviar el mensaje, revisar token o permisos")
            return False

    except Exception as exception:
        print(f"❌ Error al enviar mensaje: {exception}")
        return False
