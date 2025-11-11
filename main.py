from fastapi import FastAPI, HTTPException, Request
from utils.get_type_message import get_message_type
from utils.send_message import send_message_whatsapp

app = FastAPI()

@app.get("/welcome")
def index():
    return {"mensaje": "welcome developer"}

# Este token es solo para la verificación inicial del webhook (no es el de envío)
VERIFY_TOKEN = "EAALZCWMF3l0cBP4ZBZCUAZBaHpco2fgDuX76oZCKiEmTFjROjRuV0ZB8rVPkFq9hWkOYgrTzZAr4vx5nQXiDq0YyVt6JrF7qiC6wxFiTHrZB8MF6NpVyFKZC99N1i2w2zZAtYpu6QNxv8lTGTDzDFnZBZC9ZAHZAzB22lgSP4c7omSsNUwYiqN1G6YbMDyAZArSxZAYFgQZDZD"

@app.get("/whatsapp")
async def verify_token(request: Request):
    try:
        query_params = request.query_params
        verify_token = query_params.get("hub.verify_token")
        challenge = query_params.get("hub.challenge")

        print("🔍 Verificando token del webhook...")

        if verify_token and challenge and verify_token == VERIFY_TOKEN:
            print("✅ Verificación correcta")
            return int(challenge)
        else:
            print("❌ Token inválido o faltante")
            raise HTTPException(status_code=400, detail="Token de verificación inválido o parámetros faltantes")

    except Exception as e:
        print(f"⚠️ Error en la verificación: {e}")
        raise HTTPException(status_code=400, detail=f"Error en la verificación: {e}")

@app.post("/whatsapp")
async def received_message(request: Request):
    try:
        body = await request.json()
        print(f"📩 Webhook recibido: {body}")

        entry = body["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        if "messages" in value and len(value["messages"]) > 0:
            message = value["messages"][0]
            type_message, content = get_message_type(message)
            number = message["from"]

            print(f"💬 Mensaje recibido de {number}: Tipo={type_message}, Contenido={content}")

            if type_message == "text":
                ok = send_message_whatsapp(f"Recibí tu mensaje: {content}", number)
                print("📤 Mensaje enviado correctamente" if ok else "⚠️ No se pudo enviar el mensaje")

        return "EVENT_RECEIVED"

    except Exception as e:
        print(f"⚠️ Error procesando el mensaje: {e}")
        return "EVENT_RECEIVED"

if __name__ == "__main__":
    import uvicorn
    print("🚀 Iniciando servidor FastAPI en puerto 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
