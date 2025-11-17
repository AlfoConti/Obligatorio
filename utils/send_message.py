# utils/send_message.py
import requests

# token y phone number id reales (ajustados)
ACCESS_TOKEN = "EAALZCWMF3l0cBP4ZBZCUAZBaHpco2fgDuX76oZCKiEmTFjROjRuV0ZB8rVPkFq9hWkOYgrTzZAr4vx5nQXiDq0YyVt6JrF7qiC6wxFiTHrZB8MF6NpVyFKZC99N1i2w2zZAtYpu6QNxv8lTGTDzDFnZBZC9ZAHZAzB22lgSP4c7omSsNUwYiqN1G6YbMDyAZArSxZAYFgQZDZD"
PHONE_NUMBER_ID = "846928765173274"   # <-- ID correcto que recibiste en webhook

META_MESSAGES_URL = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"

def send_whatsapp_message(to: str, message: str) -> int:
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    try:
        r = requests.post(META_MESSAGES_URL, json=payload, headers=headers, timeout=10)
        print("send_whatsapp_message:", r.status_code, r.text)
        return r.status_code
    except Exception as e:
        print("Error send_whatsapp_message:", e)
        return 500
