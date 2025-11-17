# main.py
import os
from fastapi import FastAPI, Request
import uvicorn
from utils.get_type_message import get_message_type
from utils.send_message import send_whatsapp_message
from utils.cart_management import CartManager
from algorithms.catalog_logic import Catalog
from algorithms.delivery_manager import DeliveryManager
from utils.geo_calculator import haversine_km

app = FastAPI()

VERIFY_TOKEN = "pepito123"
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID", "491852447346105")

# Instancias globales (memoria)
catalog = Catalog()                 # carga productos desde data/products_dataset.json si existe
carts = CartManager()               # gestiona carritos por teléfono
delivery_manager = DeliveryManager()# colas, tandas, deliveries

@app.get("/welcome")
def welcome():
    return {"mensaje": "welcome developer"}

@app.get("/webhook")
async def verify(request: Request):
    params = dict(request.query_params)
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return int(challenge)
    return {"error": "Token inválido"}

@app.post("/webhook")
async def webhook(request: Request):
    payload = await request.json()
    # Extract message safe
    try:
        entry = payload.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
    except Exception:
        print("Webhook: payload con formato inesperado:", payload)
        return "EVENT_RECEIVED"

    messages = value.get("messages", [])
    if not messages:
        return "EVENT_RECEIVED"

    message = messages[0]
    sender = message.get("from")
    create_user_if_not_exists = carts.create_user_if_not_exists
    create_user_if_not_exists(sender)  # asegurar usuario

    msg_type, content = get_message_type(message)

    # Texto
    if msg_type == "text":
        text = content.strip()
        # comandos globales
        if text.lower() in ["menu", "inicio"]:
            carts.reset_browse(sender)
            send_whatsapp_message(sender, catalog.format_menu_page(sender))
            return "EVENT_RECEIVED"

        # delegar al manejador de carrito/flow
        response = handle_text_flow(sender, text, catalog, carts, delivery_manager)
        if response:
            send_whatsapp_message(sender, response)
        return "EVENT_RECEIVED"

    # Ubicación
    if msg_type == "location":
        lat, lon = content
        # confirmar orden si tenía carrito pendiente de confirmación
        response = handle_location_flow(sender, lat, lon, carts, delivery_manager)
        if response:
            send_whatsapp_message(sender, response)
        return "EVENT_RECEIVED"

    # Otros tipos
    send_whatsapp_message(sender, "Tipo de mensaje no soportado (prototipo).")
    return "EVENT_RECEIVED"

# --- Flows delegados (ligeros) ---
def handle_text_flow(phone, text, catalog, carts, delivery_manager):
    u = carts.get_user(phone)

    # navegación de catálogo
    if text.lower().startswith("siguientes"):
        u["page"] += 1
        return catalog.format_menu_page(phone)

    if text.lower().startswith("volver al inicio"):
        carts.reset_browse(phone)
        return catalog.format_menu_page(phone)

    if text.lower().startswith("volver"):
        if u["page"] > 0:
            u["page"] -= 1
        return catalog.format_menu_page(phone)

    if text.lower().startswith("filtrar"):
        # "Filtrar pizzas"
        parts = text.split(maxsplit=1)
        if len(parts) == 2:
            category = parts[1].strip().capitalize()
            if category in catalog.get_categories():
                u["filter"] = category
                u["page"] = 0
                return catalog.format_menu_page(phone)
            else:
                return f"Categorías válidas: {', '.join(catalog.get_categories())}"
        return "Usa: Filtrar <categoria>"

    if text.lower().startswith("ordenar"):
        u["sort_asc"] = not u["sort_asc"]
        return catalog.format_menu_page(phone)

    if text.lower().startswith("seleccionar"):
        parts = text.split()
        if len(parts) >= 2 and parts[1].isdigit():
            idx = int(parts[1]) - 1
            page_items = catalog.get_page_items(phone)
            if 0 <= idx < len(page_items):
                product = page_items[idx]
                u["temp_selection"] = {"product": product, "step": "qty"}
                return f"Seleccionado {product['name']}. Indica cantidad (número)."
            return "Selección inválida en esta página."
        return "Usa: Seleccionar <n>"

    if u.get("temp_selection") and u["temp_selection"].get("step") == "qty":
        if text.isdigit() and int(text) > 0:
            qty = int(text)
            u["temp_selection"]["qty"] = qty
            u["temp_selection"]["step"] = "details"
            return "Indica detalles (ej: sin tomate) o escribe 'sin'."
        return "Cantidad inválida. Ingresa un número."

    if u.get("temp_selection") and u["temp_selection"].get("step") == "details":
        details = "" if text.lower() == "sin" else text
        sel = u["temp_selection"]
        carts.add_to_cart(phone, sel["product"]["id"], sel["qty"], details)
        u["temp_selection"] = None
        return "Producto agregado al carrito. Escribe 'Ver carrito' para revisar."

    if text.lower() == "ver carrito":
        lines, total = carts.cart_summary(phone)
        if not lines:
            return "Tu carrito está vacío."
        return f"Carrito:\n{lines}\nTotal: ${total}\nEscribe: Quitar <n> | Seguir pidiendo | Confirmar"

    if text.lower().startswith("quitar"):
        parts = text.split()
        if len(parts) >= 2 and parts[1].isdigit():
            idx = int(parts[1]) - 1
            ok = carts.remove_from_cart(phone, idx)
            return "Producto removido." if ok else "Índice inválido."
        return "Usa: Quitar <n>"

    if text.lower() == "seguir pidiendo":
        return catalog.format_menu_page(phone)

    if text.lower() == "confirmar":
        # pedir ubicación
        carts.get_user(phone)["state"] = "waiting_for_location"
        return "Por favor comparte tu ubicación para calcular entrega."

    # admin/testing commands
    if text.lower() == "admin process":
        created = delivery_manager.process_all_queues_and_create_tandas()
        return f"Tandas creadas: {created}"

    if text.lower() == "menu":
        return catalog.format_menu_page(phone)

    return "No entendido. Escribe 'Menu' para comenzar."

def handle_location_flow(phone, lat, lon, carts, delivery_manager):
    user = carts.get_user(phone)
    if user["state"] == "waiting_for_location":
        # crear order
        order = carts.create_order_from_cart(phone, lat, lon)
        # enqueue
        delivery_manager.enqueue_order(order)
        user["state"] = "idle"
        # intentar crear tandas/asignar
        created = delivery_manager.process_all_queues_and_create_tandas()
        msg = f"Pedido creado (ID {order['id']}). Código: {order['code']}. Distancia: {order['distance_km']} km."
        if created:
            msg += f" Tandas generadas: {created}"
        return msg
    return "Ubicación recibida."

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
