import os
from fastapi import FastAPI, Request
from utils.send_message import send_text_message, send_button_message, send_list_message

app = FastAPI()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "token123")


@app.get("/")
async def home():
    return {"status": "ok", "message": "Bot WhatsApp funcionando"}


# ========= VERIFICACIÓN DEL WEBHOOK =========
@app.get("/whatsapp")
async def verify(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    challenge = params.get("hub.challenge")
    token = params.get("hub.verify_token")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return int(challenge)

    return {"error": "Token inválido"}


# ========= RECEPCIÓN DE MENSAJES =========
@app.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    data = await request.json()

    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        messages = value.get("messages", [])
        if not messages:
            return {"status": "no_messages"}

        msg = messages[0]
        user = msg["from"]

        # ==== MENSAJE DE TEXTO ====
        if msg["type"] == "text":
            text = msg["text"]["body"].lower()

            if text == "menu":
                buttons = [
                    {"id": "catalogo", "title": "Ver catálogo"},
                    {"id": "promo", "title": "Promos"},
                ]
                send_button_message(user, "¿Qué deseas hacer?", buttons)
                return {"sent": "buttons"}

            # Cualquier otro texto
            send_text_message(user, "Envia *menu* para comenzar")
            return {"sent": "text"}

        # ==== RESPUESTA A BOTONES ====
        if msg["type"] == "interactive" and "button_reply" in msg["interactive"]:
            button_id = msg["interactive"]["button_reply"]["id"]

            if button_id == "catalogo":
                sections = [
                    {
                        "title": "Categorías",
                        "rows": [
                            {"id": "hamb", "title": "Hamburguesas"},
                            {"id": "pizza", "title": "Pizzas"},
                            {"id": "bebidas", "title": "Bebidas"},
                        ]
                    }
                ]

                send_list_message(user, "Catálogo", "Selecciona una categoría:", sections)
                return {"sent": "list"}

            if button_id == "promo":
                send_text_message(user, "Hoy no hay promociones 😢")
                return {"sent": "promo"}

    except Exception as e:
        print("ERROR:", e)
        return {"error": str(e)}

    return {"status": "ok"}


# ========= EJECUCIÓN LOCAL =========
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
