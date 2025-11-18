import os
from fastapi import FastAPI, Request
from utils.send_message import send_text_message, send_button_message, send_list_message

app = FastAPI()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "token123")  # Para el webhook de Meta


@app.get("/")
async def home():
    return {"status": "ok", "message": "Bot WhatsApp funcionando"}


# ---------- WEBHOOK VERIFICACIÓN META ----------
@app.get("/webhook")
async def verify(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    challenge = params.get("hub.challenge")
    token = params.get("hub.verify_token")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return int(challenge)
    return {"error": "Token inválido"}


# ---------- RECEPCIÓN DE MENSAJES ----------
@app.post("/webhook")
async def webhook_listener(request: Request):
    data = await request.json()

    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        messages = value.get("messages", [])
        if not messages:
            return {"status": "no_messages"}

        message = messages[0]
        from_number = message["from"]

        # Texto tradicional
        if message["type"] == "text":
            text = message["text"]["body"].lower()

            if text == "menu":
                buttons = [
                    {"id": "catalogo", "title": "Ver catálogo"},
                    {"id": "ofertas", "title": "Ofertas"},
                ]
                send_button_message(from_number, "¿Qué deseas hacer?", buttons)
                return {"status": "button_sent"}

            else:
                send_text_message(from_number, "Escribe *menu* para comenzar")
                return {"status": "text_sent"}

        # Botones
        if message["type"] == "interactive":
            id = message["interactive"]["button_reply"]["id"]

            if id == "catalogo":
                sections = [
                    {
                        "title": "Catálogo",
                        "rows": [
                            {"id": "1", "title": "Hamburguesas"},
                            {"id": "2", "title": "Pizzas"},
                            {"id": "3", "title": "Bebidas"},
                        ]
                    }
                ]

                send_list_message(
                    from_number,
                    "Catálogo",
                    "Selecciona una categoría:",
                    sections
                )
                return {"status": "list_sent"}

            if id == "ofertas":
                send_text_message(from_number, "Hoy no hay ofertas 😢")
                return {"status": "ofertas_sent"}

    except Exception as e:
        print("ERROR WEBHOOK:", e)
        return {"status": "error", "detail": str(e)}

    return {"status": "ok"}
        

# ---------- INICIO SERVER LOCAL ----------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 3000)))
