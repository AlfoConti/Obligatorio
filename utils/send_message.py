# utils/send_message.py

import requests
import json
import os

# ====================================================================
# CONFIGURACIÓN (NOTA: Usar Variables de Entorno es la mejor práctica)
# ====================================================================

# Usamos los valores proporcionados por el usuario como fallback
# En un entorno de producción, DEBES asegurar estos tokens.
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "EAALZCWMF3l0cBP4ZBZCUAZBaHpco2fgDuX76oZCKiEmTFjROjRuV0ZB8rVPkFq9hWkOYgrTzZAr4vx5nQXiDq0YyVt6JrF7qiC6wxFiTHrZB8MF6NpVyFKZC99N1i2w2zZAtYpu6QNxv8lTGTDzDFnZBZC9ZAHZAzB22lgSP4c7omSsNUwYiqN1G6YbMDyAZArSxZAYFgQZDZD")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID", "846928765173274") 
API_URL = f"https://graph.facebook.com/v22.0/{WHATSAPP_PHONE_ID}/messages"

# ====================================================================
# FUNCIÓN DE ENVÍO
# ====================================================================

def send_message_whatsapp(content, recipient_number):
    """
    Envía un mensaje de WhatsApp. Puede enviar:
    1. TEXTO simple (content es un string).
    2. Mensajes INTERACTIVOS (content es un diccionario JSON para Listas/Botones).

    :param content: String o Diccionario con el payload interactivo.
    :param recipient_number: Número del cliente.
    :return: True si se envió con éxito, False en caso contrario.
    """
    
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient_number,
    }

    if isinstance(content, str):
        # 1. Envío de MENSAJE DE TEXTO simple
        payload["type"] = "text"
        payload["text"] = {"body": content}
    elif isinstance(content, dict):
        # 2. Envío de MENSAJE INTERACTIVO (Lista/Botón)
        # El diccionario 'content' se fusiona con el payload base
        payload.update(content)
    else:
        print(f"ERROR: Tipo de contenido no soportado para envío: {type(content)}")
        return False

    try:
        # Petición POST a la API de Meta
        response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status() # Lanza un error para códigos 4xx/5xx

        print(f"Mensaje enviado con éxito a {recipient_number}. Status: {response.status_code}")
        return True
        
    except requests.exceptions.HTTPError as err:
        print(f"ERROR HTTP al enviar mensaje: {err}")
        # Muestra la respuesta de Meta para depuración
        print(f"Respuesta de Meta: {getattr(response, 'text', 'No body')}") 
        return False
    except Exception as e:
        print(f"ERROR desconocido al enviar mensaje: {e}")
        return False