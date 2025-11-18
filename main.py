from fastapi import FastAPI, Request
from algorithms.catalog_logic import send_product_menu, send_filter_menu
from utils.send_message import send_text_message
import uvicorn

app = FastAPI()

SESSIONS = {}

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()

    try:
        message = data["entry"][0]["changes"][0]["value"]["messages"][0]
    except:
        return {"status": "ignored"}

    number = message["from"]

    if number not in SESSIONS:
        SESSIONS[number] = {"page": 0, "category": "Todos", "order": "none"}
        send_text_message(number, "¡Hola! Bienvenido al restaurante 🍔")
        send_product_menu(number)
        return {"status": "ok"}

    msg_type = message.get("type")

    if msg_type == "interactive":
        inter = message["interactive"]

        if inter["type"] == "button_reply":
            button_id = inter["button_reply"]["id"]
            return {"status": "ok"}

        elif inter["type"] == "list_reply":
            selection = inter["list_reply"]["id"]

            # Filtrar
            if selection == "filter-menu":
                send_filter_menu(number)
                return {"status": "ok"}

            # Ordenar
            if selection == "order-price":
                if SESSIONS[number]["order"] == "asc":
                    SESSIONS[number]["order"] = "desc"
                else:
                    SESSIONS[number]["order"] = "asc"
                send_product_menu(number)
                return {"status": "ok"}

            # Categorías
            if selection.startswith("cat-"):
                SESSIONS[number]["category"] = selection.replace("cat-", "")
                SESSIONS[number]["page"] = 0
                send_product_menu(number)
                return {"status": "ok"}

            # Navegación
            if selection.startswith("next-"):
                SESSIONS[number]["page"] += 1
                send_product_menu(number)
                return {"status": "ok"}

            if selection.startswith("back-"):
                SESSIONS[number]["page"] -= 1
                send_product_menu(number)
                return {"status": "ok"}

            if selection == "back-home":
                SESSIONS[number] = {"page": 0, "category": "Todos", "order": "none"}
                send_product_menu(number)
                return {"status": "ok"}

            # Producto elegido
            if selection.startswith("product-"):
                prod_id = selection.replace("product-", "")
                send_text_message(number, f"Elegiste el producto {prod_id}")
                return {"status": "ok"}

    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3000)
