from flask import Flask, request
from algorithms.catalog_logic import send_product_menu, send_filter_menu
from utils.send_message import send_text_message
import json

app = Flask(__name__)

SESSIONS = {} 
"""
SESSIONS[number] = {
    "page": 0,
    "category": "Todos",
    "order": "none"
}
"""

@app.post("/webhook")
def webhook():
    data = request.json

    try:
        message = data["entry"][0]["changes"][0]["value"]["messages"][0]
    except:
        return "ok", 200

    number = message["from"]

    if number not in SESSIONS:
        SESSIONS[number] = {"page": 0, "category": "Todos", "order": "none"}
        send_text_message(number, "¡Hola! Bienvenido al restaurante 🍔")
        send_product_menu(number)
        return "ok"

    msg_type = message.get("type")

    # -----------------------------------------
    # BOTÓN o LISTA (interactive)
    # -----------------------------------------
    if msg_type == "interactive":
        inter = message["interactive"]

        # BUTTON
        if inter["type"] == "button_reply":
            button_id = inter["button_reply"]["id"]
            # Aquí puedes agregar más botones
            return "ok"

        # LIST
        elif inter["type"] == "list_reply":
            selection = inter["list_reply"]["id"]

            # Filtrar
            if selection == "filter-menu":
                send_filter_menu(number)
                return "ok"

            # Ordenamiento
            if selection == "order-price":
                # toggle
                if SESSIONS[number]["order"] == "asc":
                    SESSIONS[number]["order"] = "desc"
                else:
                    SESSIONS[number]["order"] = "asc"
                send_product_menu(
                    number,
                    SESSIONS[number]["page"],
                    SESSIONS[number]["category"],
                    SESSIONS[number]["order"]
                )
                return "ok"

            # Categorías
            if selection.startswith("cat-"):
                cat = selection.replace("cat-", "")
                SESSIONS[number]["category"] = cat
                SESSIONS[number]["page"] = 0
                send_product_menu(number, 0, cat)
                return "ok"

            # Navegación
            if selection.startswith("next-"):
                page = int(selection.replace("next-", ""))
                SESSIONS[number]["page"] = page
                send_product_menu(number, page, SESSIONS[number]["category"], SESSIONS[number]["order"])
                return "ok"

            if selection.startswith("back-"):
                page = int(selection.replace("back-", ""))
                SESSIONS[number]["page"] = page
                send_product_menu(number, page, SESSIONS[number]["category"], SESSIONS[number]["order"])
                return "ok"

            if selection == "back-home":
                SESSIONS[number]["page"] = 0
                send_product_menu(number, 0)
                return "ok"

            # Producto seleccionado
            if selection.startswith("product-"):
                prod_id = int(selection.replace("product-", ""))
                send_text_message(number, f"Elegiste el producto {prod_id}. Enviaré lógica de cantidad luego.")
                return "ok"

    return "ok"


if __name__ == "__main__":
    app.run(port=3000)
