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
        token = "EAALZCWMF3l0cBP4ZBZCUAZBaHpco2fgDuX76oZCKiEmTFjROjRuV0ZB8rVPkFq9hWkOYgrTzZAr4vx5nQXiDq0YyVt6JrF7qiC6wxFiTHrZB8MF6NpVyFKZC99N1i2w2zZAtYpu6QNxv8lTGTDzDFnZBZC9ZAHZAzB22lgSP4c7omSsNUwYiqN1G6YbMDyAZArSxZAYFgQZDZD" # Obtener de variables de entorno o configuración segura
        api_url = "https://graph.facebook.com/v22.0/846928765173274/messages" # Obtener de variables de entorno o configuración segura
        data = generate_data(text_user, number_user)
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
        
        response = requests.post(api_url, data=json.dumps(data), headers=headers)
        
        if response.status_code == 200:
            return True
        
        return False
    except Exception as exception:
        print(exception)
        return False