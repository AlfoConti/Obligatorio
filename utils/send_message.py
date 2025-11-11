import requests
import json

# LÍNEA 70
def generate_data(text_user, number_user):
    return {
        "messaging_product": "whatsapp",
        "to": number_user,
        "text": {
            "body": text_user
        },
        "type": "text"
    }
# LÍNEA 79
def send_message_whatsapp(text_user, number_user):
    try:
        token = "" # Obtener de variables de entorno o configuración segura
        api_url = "" # Obtener de variables de entorno o configuración segura
        data = generate_data(text_user, number_user)
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
        
        response = requests.post(api_url, data=json.dumps(data), headers=headers)
        
        if response.status_code == 200:
            return True
        
        return False
    except Exception as exception:
        print(exception)
        return False
    