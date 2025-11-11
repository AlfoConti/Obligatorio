from fastapi import FastAPI, HTTPException, Request
from utils.get_type_message import get_message_type
from utils.send_message import send_message_whatsapp
import os
import uvicorn

app = FastAPI()

@app.get("/welcome")
def index():
    return {"mensaje": "welcome developer"}

# ⚠️ TOKENES: NO SON LO MISMO
VERIFY_TOKEN = "mi_token_de_verificacion"  # Token que pones en Meta Developers
ACCESS_TOKEN = "EAALZCWMF3l0cBP4ZBZCUAZBaHpco2fgDuX76oZCKiEmTFjROjRuV0ZB8rVPkFq9hWkOYgrTzZAr4vx5nQXiDq0YyVt6JrF7qiC6wxFiTHrZB8MF6NpVyFKZC99N1i2w2zZAtYpu6QNxv8lTGTDzDFnZBZC9ZAHZAzB22lgSP4c7omSsNUwYiqN1G6YbMDyAZArSxZAYFgQZDZD"

@app.get("/whatsapp")
async def verify_token(request: Request):
    try:
        query_params = request.query_params
        verify_token = query_params.get("hub.verify_token")
        challenge = query_params.get("hub.challenge")

        if verify_token == VERIFY_TOKEN:
            # Devuelve el challenge como texto plano
            return int(challenge)
        else:
            raise HTTPException(status_code=403, detail="Token de verificación inválido")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error en la verificación: {e}")

@app.post("/whatsapp")
async def received_message(request: Request):
    try:
        body = await request.json()
        entry = body.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
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
        # Meta requiere siempre 200 aunque haya error
        return "EVENT_RECEIVED"

if __name__ == "__main__":
    # Render asigna el puerto automáticamente
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
