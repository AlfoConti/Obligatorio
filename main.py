import os
from fastapi import FastAPI, Request
import uvicorn
import requests

ACCESS_TOKEN = "EAALZCWMF3l0cBP4ZBZCUAZBaHpco2fgDuX76oZCKiEmTFjROjRuV0ZB8rVPkFq9hWkOYgrTzZAr4vx5nQXiDq0YyVt6JrF7qiC6wxFiTHrZB8MF6NpVyFKZC99N1i2w2zZAtYpu6QNxv8lTGTDzDFnZBZC9ZAHZAzB22lgSP4c7omSsNUwYiqN1G6YbMDyAZArSxZAYFgQZDZD"
VERIFY_TOKEN = "pepito123"

app = FastAPI()

# ------------------------------------------
# VERIFICACIÓN DEL WEBHOOK (GET)
# ------------------------------------------
@app.get("/whatsapp")
async def verify(request: Request):
    params = dict(request.query_params)
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return int(challenge)
    else:
        return {"error": "Token inválido"}

# ------------------------------------------
# RECEPCIÓN DE MENSAJES (POST)
# ------------------------------------------
@app.post("/whatsapp")
async def webhook(request: Request):
    body = await request.json()
    print("Webhook recibido:", body)

    try:
        entry = body["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        if "messages" not in value:
            print("No hay mensajes.")
            return {"status": "no_messages"}

        message = value["messages"][0]

        sender = message["from"]

        # texto recibido
        if "text" in message:
            text = message["text"]["body"]

            # 👉 AQUÍ ENVIAMOS EL MENÚ
            menu = (
                "🍔 *Bienvenido al BK Bot*\n"
                "1️⃣ Ver menú\n"
                "2️⃣ Mi carrito\n"
                "3️⃣ Realizar pedido\n"
                "0️⃣ Hablar con un operador"
            )

            responder(sender, menu)

    except Exception as e:
        print("Error procesando mensaje:", e)

    return {"status": "ok"}

# ------------------------------------------
# FUNCIÓN PARA RESPONDER
# ------------------------------------------
def responder(to, texto):
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {"body": texto}
    }

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    url = "https://graph.facebook.com/v19.0/491852447346105/messages"
    r = requests.post(url, json=data, headers=headers)

    print("Respuesta de Meta:", r.text)

# ------------------------------------------
# RUN SERVER
# ------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
