from fastapi import FastAPI, HTTPException, Request
from utils.get_type_message import get_message_type
from utils.send_message import send_whatsapp_message
import os
import uvicorn

app = FastAPI()

@app.get("/welcome")
def index():
    return {"mensaje": "welcome developer"}


# === VARIABLES SEGURAS ===
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "mi_token_de_verificacion")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")


@app.get("/whatsapp")
async def verify_token(request: Request):
    """
    Webhook verification for Meta (GET)
    """
    try:
        verify_token = request.query_params.get("hub.verify_token")
        challenge = request.query_params.get("hub.challenge")

        if verify_token == VERIFY_TOKEN:
            return int(challenge)
        else:
            raise HTTPException(status_code=403, detail="Token inválido")

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error en verificación: {e}")


@app.post("/whatsapp")
async def received_message(request: Request):
    """
    Webhook for receiving WhatsApp messages (POST)
    """
    try:
        body = await request.json()

        entry = body.get("entry", [])
        if not entry:
            return "EVENT_RECEIVED"

        changes = entry[0].get("changes", [])
        if not changes:
            return "EVENT_RECEIVED"

        value = changes[0].get("value", {})

        messages = value.get("messages")
        if not messages:
            return "EVENT_RECEIVED"

        msg = messages[0]
        number = msg["from"]

        type_msg, content = get_message_type(msg)
        print(f"📩 Mensaje recibido de {number} | Tipo: {type_msg} | Contenido: {content}")

        if type_msg == "text":
            send_whatsapp_message(number, content)

        return "EVENT_RECEIVED"

    except Exception as e:
        print("❌ Error procesando mensaje:", e)
        return "EVENT_RECEIVED"


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
