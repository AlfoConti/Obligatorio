# main.py
from flask import Flask, request, jsonify

# Importar utilidades REALES de tu proyecto
from utils.send_message import (
    send_text_message,
    send_list_message,
    send_button_message,
)
from utils.get_type_message import get_payload_type
from utils.cart_management import CartManager
from utils.whatsapp_parser import parse_incoming
from algorithms.catalog_logic import CatalogManager
from algorithms.delivery_manager import DeliveryManager

app = Flask(__name__)

# Instancias globales del sistema
catalog = CatalogManager()
delivery = DeliveryManager()

# Carritos por usuario (sender ID)
user_carts = {}


@app.route("/webhook", methods=["GET"])
def verify():
    """Meta envía challenge al crear el webhook.
       NO usa VERIFY_TOKEN porque vos pediste sin token."""
    return request.args.get("hub.challenge", "")


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    # Extraer datos claves del mensaje recibido
    sender, message_type, payload = parse_incoming(data)

    # Si no es mensaje válido
    if sender is None:
        return jsonify({"status": "ignored"})

    # Crear carrito si no existe
    if sender not in user_carts:
        user_carts[sender] = CartManager()
    cart = user_carts[sender]

    # Obtener acción de acuerdo al tipo/value
    action, value = get_payload_type(message_type, payload)

    # ───────────────────────────────
    # SECCIÓN: CATÁLOGO (BOTÓN / LISTA)
    # ───────────────────────────────
    if action == "OPEN_CATALOG":
        sections = catalog.build_list_page(0)
        send_list_message(sender, "Catálogo", "Seleccioná un producto", sections)
        return jsonify({"status": "ok"})

    if action == "NEXT_PAGE":
        page = int(value)
        sections = catalog.build_list_page(page)
        send_list_message(sender, "Catálogo", "Más productos", sections)
        return jsonify({"status": "ok"})

    if action == "PREV_PAGE":
        page = int(value)
        sections = catalog.build_list_page(page)
        send_list_message(sender, "Catálogo", "Página anterior", sections)
        return jsonify({"status": "ok"})

    if action == "SHOW_PRODUCT":
        product = catalog.get_product(int(value))
        if product:
            buttons = [
                {"id": f"ADD_CART:{product['id']}", "title": "Agregar al carrito"},
                {"id": "OPEN_CATALOG", "title": "Volver"},
            ]
            txt = (
                f"*{product['name']}*\n"
                f"Precio: ${product['price']}\n\n"
                f"{product['description']}"
            )
            send_button_message(sender, txt, buttons)
        return jsonify({"status": "ok"})

    # ───────────────────────────────
    # SECCIÓN: CARRITO
    # ───────────────────────────────
    if action == "ADD_CART":
        product = catalog.get_product(int(value))
        if product:
            cart.add_item(product)
            send_text_message(sender, f"🛒 {product['name']} agregado al carrito.")
        return jsonify({"status": "ok"})

    if action == "SHOW_CART":
        send_text_message(sender, cart.render_cart())
        return jsonify({"status": "ok"})

    # ───────────────────────────────
    # SECCIÓN: MENSAJES NORMALES
    # ───────────────────────────────
    if message_type == "text":
        text = payload.lower()

        if text in ["menu", "catalogo"]:
            sections = catalog.build_list_page(0)
            send_list_message(sender, "Catálogo", "Elegí un producto", sections)
            return jsonify({"status": "ok"})

        if text == "carrito":
            send_text_message(sender, cart.render_cart())
            return jsonify({"status": "ok"})

        send_text_message(sender, "Hola! Escribí *catalogo* o *carrito*.")
        return jsonify({"status": "ok"})

    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(port=5000, debug=True)
