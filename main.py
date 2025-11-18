from fastapi import FastAPI, Request
from utils.send_message import (
    send_text_message,
    send_button_message,
    send_list_message
)

app = FastAPI()

@app.get("/")
def root():
    return {"status": "running"}

@app.post("/whatsapp")
async def whatsapp_webhook(request: Request):

    body = await request.json()

    # Seguridad: si no viene mensaje, ignoramos
    try:
        entry = body["entry"][0]["changes"][0]["value"]
        message = entry["messages"][0]
        number = message["from"]
    except:
        return {"status": "ignored"}

    # Caso: Botón o texto
    text = ""
    if message.get("text"):
        text = message["text"]["body"].strip().lower()

    if message.get("interactive"):
        interactive = message["interactive"]
        if "button_reply" in interactive:
            text = interactive["button_reply"]["id"]
        elif "list_reply" in interactive:
            text = interactive["list_reply"]["id"]

    # 🟦 PRIMER MENSAJE
    if text == "hola" or text == "menu" or text == "":
        send_button_message(
            number,
            "¡Hola! ¿Qué deseas hacer?",
            buttons=[
                {"id": "ver_menu", "title": "📜 Ver Menú"},
                {"id": "hacer_pedido", "title": "🛒 Hacer Pedido"}
            ]
        )
        return {"status": "sent"}

    # 🟧 SI ELIGE "VER MENÚ"
    if text == "ver_menu":
        send_list_message(
            number,
            header="Menú del día",
            body="Selecciona una categoría:",
            sections=[
                {
                    "title": "Comidas",
                    "rows": [
                        {"id": "menu_hamburguesas", "title": "🍔 Hamburguesas"},
                        {"id": "menu_pizzas", "title": "🍕 Pizzas"},
                    ]
                }
            ]
        )
        return {"status": "sent"}

    # 🟩 SUBMENÚ: Hamburguesas
    if text == "menu_hamburguesas":
        send_text_message(number, "🍔 Menú Hamburguesas:\n- Clásica\n- Doble\n- BBQ")
        return {"status": "sent"}

    # 🟥 SUBMENÚ: Pizzas
    if text == "menu_pizzas":
        send_text_message(number, "🍕 Menú Pizzas:\n- Muzza\n- Pepperoni\n- 4 Quesos")
        return {"status": "sent"}

    return {"status": "unknown"}
