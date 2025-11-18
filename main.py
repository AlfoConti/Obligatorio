from fastapi import FastAPI, Request
import os

from utils.send_message import send_whatsapp_message
from utils.get_type_message import get_message_type

app = FastAPI()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")


# ========= WEBHOOK VERIFICATION ==========
@app.get("/webhook")
async def verify_token(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("Webhook verificado correctamente.")
        return int(challenge)

    return {"error": "TOKEN_INVALIDO"}


# ========= RECEIVING WHATSAPP MESSAGES ==========
@app.post("/webhook")
async def receive_message(request: Request):
    body = await request.json()
    print("WEBHOOK BODY:", body)

    try:
        entry = body["entry"][0]["changes"][0]["value"]

        if "messages" in entry:
            message = entry["messages"][0]
            from_number = message["from"]

            msg_type, content = get_message_type(message)
            print(f"Mensaje recibido → Tipo: {msg_type} | Contenido: {content}")

            if msg_type == "text":
                send_whatsapp_message(from_number, f"Recibí tu mensaje: {content}")

            elif msg_type == "button":
                send_whatsapp_message(from_number, f"Has presionado: {content}")

            elif msg_type == "list":
                send_whatsapp_message(from_number, f"Elegiste la opción: {content}")

            else:
                send_whatsapp_message(from_number, "No entendí tu mensaje.")

    except Exception as e:
        print("ERROR PROCESANDO WHATSAPP:", e)

    return {"status": "ok"}
