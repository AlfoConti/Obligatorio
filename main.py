from fastapi import FastAPI, HTTPException, Request
from utils.get_type_message import get_message_type
from utils.send_message import send_message_whatsapp
import os

app = FastAPI()

@app.get("/welcome")
def index():
    return {"mensaje": "welcome developer"}

# ⚠️ TOKENES
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "mi_token_de_verificacion")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN", "")

@app.get("/whatsapp")
async def verify_token(request: Request):
    query_params = request.query_params
    verify_token = query_params.get("hub.verify_token")
    challenge = query_params.get("hub.challenge")

    if verify_token == VERIFY_TOKEN:
        return int(challenge)
    else:
        raise HTTPException(status_code=403, detail="Token de verificación inválido")


@app.post("/whatsapp")
async def received_message(request: Request):
    try:
        body = await request.json()

        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})

        if "messages" in value and len(value["messages"]) > 0:
            message = value["messages"][0]
            type_message, content = get_message_type(message)
            number = message["from"]

            print(f"Mensaje recibido de {number}: Tipo: {type_message}, Contenido: {content}")

            if type_message == "text":
                send_message_whatsapp(content, number)

        return "EVENT_RECEIVED"

    except Exception as e:
        print(f"Error procesando mensaje: {e}")
        return "EVENT_RECEIVED"
