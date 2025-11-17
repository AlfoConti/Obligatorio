# main.py
import os
from fastapi import FastAPI, Request
import uvicorn
from utils.get_type_message import get_message_type
from utils.send_message import send_whatsapp_message
from utils.cart_management import CartManager
from algorithms.catalog_logic import Catalog
from algorithms.delivery_manager import DeliveryManager
from algorithms.catalog_logic import Catalog  # noqa: F811

app = FastAPI()

VERIFY_TOKEN = "pepito123"  # el que usás en Meta

# instancias en memoria
catalog = Catalog()                      # carga data/products_dataset.json si existe
carts = CartManager(product_lookup=catalog.get_product_by_id)
delivery_manager = DeliveryManager(restaurant_coord=catalog.get_restaurant_coord())

@app.get("/welcome")
def welcome():
    return {"mensaje": "welcome developer"}

@app.get("/whatsapp")
async def verify(request: Request):
    params = dict(request.query_params)
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return int(challenge)
    return {"error": "Token inválido"}

@app.post("/whatsapp")
async def webhook(request: Request):
    payload = await request.json()
    print("Webhook received:", payload)
    try:
        entry = payload.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
    except Exception:
        print("Payload inesperado")
        return "EVENT_RECEIVED"

    messages = value.get("messages", [])
    if not messages:
        return "EVENT_RECEIVED"

    message = messages[0]
    sender = message.get("from")
    # ensure user exists
    carts.create_user_if_not_exists(sender)

    msg_type, content = get_message_type(message)

    if msg_type == "text":
        text = content.strip()
        resp = handle_text_flow(sender, text)
        if resp:
            send_whatsapp_message(sender, resp)
        return "EVENT_RECEIVED"

    if msg_type == "location":
        lat, lon = content
        resp = handle_location_flow(sender, lat, lon)
        if resp:
            send_whatsapp_message(sender, resp)
        return "EVENT_RECEIVED"

    send_whatsapp_message(sender, "Tipo de mensaje no soportado en el prototipo.")
    return "EVENT_RECEIVED"

# -------------------------
# Flow handlers
# -------------------------
def handle_text_flow(phone, text):
    u = carts.get_user(phone)

    # comandos globales
    if text.lower() in ["menu", "inicio"]:
        u["page"] = 0
        return catalog.format_menu_page_for_user_state(u)

    if text.lower() == "siguientes":
        u["page"] += 1
        return catalog.format_menu_page_for_user_state(u)

    if text.lower() == "volver":
        if u["page"] > 0:
            u["page"] -= 1
        return catalog.format_menu_page_for_user_state(u)

    if text.lower().startswith("filtrar"):
        parts = text.split(maxsplit=1)
        if len(parts) == 2:
            cat = parts[1].strip().capitalize()
            if cat in catalog.get_categories():
                u["filter"] = cat
                u["page"] = 0
                return catalog.format_menu_page_for_user_state(u)
            return f"Categorías válidas: {', '.join(catalog.get_categories())}"
        return "Usa: Filtrar <categoria>"

    if text.lower() == "ordenar":
        u["sort_asc"] = not u["sort_asc"]
        return catalog.format_menu_page_for_user_state(u)

    if text.lower().startswith("seleccionar"):
        parts = text.split()
        if len(parts) >= 2 and parts[1].isdigit():
            idx = int(parts[1]) - 1
            items = catalog.get_page_items_for_state(u)
            if 0 <= idx < len(items):
                p = items[idx]
                u["temp_selection"] = {"product": p, "step": "qty"}
                return f"Seleccionado {p['name']}. Indica cantidad (número)."
            return "Selección inválida."
        return "Usa: Seleccionar <n>"

    if u.get("temp_selection") and u["temp_selection"].get("step") == "qty":
        if text.isdigit() and int(text) > 0:
            qty = int(text)
            u["temp_selection"]["qty"] = qty
            u["temp_selection"]["step"] = "details"
            return "Indica detalles (ej: sin tomate) o escribe 'sin'."
        return "Cantidad inválida."

    if u.get("temp_selection") and u["temp_selection"].get("step") == "details":
        details = "" if text.lower() == "sin" else text
        sel = u["temp_selection"]
        carts.add_to_cart(phone, sel["product"]["id"], sel["qty"], details)
        u["temp_selection"] = None
        return "Producto agregado. Escribe 'Ver carrito' para revisar."

    if text.lower() == "ver carrito":
        lines, total = carts.cart_summary(phone)
        if not lines:
            return "Tu carrito está vacío."
        return f"Carrito:\n{lines}\nTotal: ${total}\nComandos: Quitar <n> | Seguir pidiendo | Confirmar"

    if text.lower().startswith("quitar"):
        parts = text.split()
        if len(parts) >= 2 and parts[1].isdigit():
            ok = carts.remove_from_cart(phone, int(parts[1]) - 1)
            return "Producto eliminado." if ok else "Índice inválido."
        return "Usa: Quitar <n>"

    if text.lower() == "seguir pidiendo":
        return catalog.format_menu_page_for_user_state(u)

    if text.lower() == "confirmar":
        u["state"] = "waiting_for_location"
        return "Por favor comparte tu ubicación para calcular entrega."

    if text.lower() == "admin process":
        created = delivery_manager.process_all_queues_and_create_tandas(carts.orders)
        return f"Tandas creadas: {created}"

    return "No entendido. Escribe 'Menu' para comenzar."

def handle_location_flow(phone, lat, lon):
    u = carts.get_user(phone)
    if u["state"] == "waiting_for_location":
        order = carts.create_order_from_cart(phone, lat, lon)
        delivery_manager.enqueue_order(order)
        u["state"] = "idle"
        created = delivery_manager.process_all_queues_and_create_tandas(carts.orders)
        msg = f"Pedido creado (ID {order['id']}). Código: {order['code']}. Distancia: {order.get('distance_km')} km."
        if created:
            msg += f" Tandas generadas: {created}"
        return msg
    return "Ubicación recibida."

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
