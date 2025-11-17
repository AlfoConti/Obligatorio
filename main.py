# main.py
import os
from fastapi import FastAPI, Request
import uvicorn
from utils.get_type_message import get_message_type
from utils.send_message import send_whatsapp_message
from utils.cart_management import CartManager
from algorithms.catalog_logic import Catalog
from algorithms.delivery_manager import DeliveryManager

app = FastAPI()

VERIFY_TOKEN = "pepito123"

# -----------------------------
# INSTANCIAS
# -----------------------------
catalog = Catalog()
carts = CartManager(product_lookup=catalog.get_product_by_id)

# si no existe coordenada en Catalog, usamos una fija
try:
    restaurant_coord = catalog.get_restaurant_coord()
except Exception:
    restaurant_coord = (-34.9011, -56.1645)

delivery_manager = DeliveryManager(restaurant_coord=restaurant_coord)


@app.get("/welcome")
def welcome():
    return {"mensaje": "welcome developer"}


# -----------------------------
# VERIFICACIÓN WHATSAPP
# -----------------------------
@app.get("/whatsapp")
async def verify(request: Request):
    params = dict(request.query_params)
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return int(challenge)
    return {"error": "Token inválido"}


# -----------------------------
# WEBHOOK
# -----------------------------
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

    carts.create_user_if_not_exists(sender)
    msg_type, content = get_message_type(message)

    if msg_type == "text":
        resp = handle_text_flow(sender, content.strip())
        if resp:
            send_whatsapp_message(sender, resp)
        return "EVENT_RECEIVED"

    if msg_type == "location":
        lat, lon = content
        resp = handle_location_flow(sender, lat, lon)
        if resp:
            send_whatsapp_message(sender, resp)
        return "EVENT_RECEIVED"

    send_whatsapp_message(sender, "Tipo de mensaje no soportado.")
    return "EVENT_RECEIVED"


# -------------------------------------------------
#   LÓGICA DEL FLUJO
# -------------------------------------------------
def handle_text_flow(phone, text):
    u = carts.get_user(phone)

    # ---------------------------
    # MENU SIMPLE (sin paginado)
    # ---------------------------
    if text.lower() in ["menu", "inicio"]:
        cats = catalog.get_categories()
        msg = "📦 *Categorías disponibles:*\n\n"
        for c in cats:
            msg += f"• {c}\n"
        msg += "\nUsa: *Filtrar <categoria>* para ver productos."
        return msg

    if text.lower().startswith("filtrar"):
        parts = text.split(maxsplit=1)
        if len(parts) == 2:
            cat = parts[1].strip()
            products = catalog.get_products_by_category(cat)
            if not products:
                return f"No existe la categoría '{cat}'."
            u["last_list"] = products
            msg = f"📦 *Productos en {cat}:*\n\n"
            for idx, p in enumerate(products, start=1):
                msg += f"{idx}. {p['name']} - ${p['price']}\n"
            msg += "\nUsa: *Seleccionar <n>*"
            return msg
        return "Usa: Filtrar <categoria>"

    # ---------------------------
    # SELECCIÓN DE PRODUCTO
    # ---------------------------
    if text.lower().startswith("seleccionar"):
        parts = text.split()
        if len(parts) >= 2 and parts[1].isdigit():
            idx = int(parts[1]) - 1
            items = u.get("last_list", [])
            if 0 <= idx < len(items):
                p = items[idx]
                u["temp_selection"] = {"product": p, "step": "qty"}
                return f"Seleccionado {p['name']}. Indica cantidad:"
            return "Selección inválida."
        return "Usa: Seleccionar <n>"

    # cantidad
    if u.get("temp_selection") and u["temp_selection"]["step"] == "qty":
        if text.isdigit() and int(text) > 0:
            qty = int(text)
            u["temp_selection"]["qty"] = qty
            u["temp_selection"]["step"] = "details"
            return "Indica detalles (o escribe 'sin'):"
        return "Cantidad inválida."

    # detalles
    if u.get("temp_selection") and u["temp_selection"]["step"] == "details":
        details = "" if text.lower() == "sin" else text
        sel = u["temp_selection"]
        carts.add_to_cart(phone, sel["product"]["id"], sel["qty"], details)
        u["temp_selection"] = None
        return "Producto agregado. Escribe 'Ver carrito' para revisar."

    # ---------------------------
    # CARRITO
    # ---------------------------
    if text.lower() == "ver carrito":
        lines, total = carts.cart_summary(phone)
        if not lines:
            return "Tu carrito está vacío."
        return f"Carrito:\n{lines}\nTotal: ${total}\n\nComandos: Quitar <n> | Confirmar"

    if text.lower().startswith("quitar"):
        parts = text.split()
        if len(parts) >= 2 and parts[1].isdigit():
            ok = carts.remove_from_cart(phone, int(parts[1]) - 1)
            return "Producto eliminado." if ok else "Índice inválido."
        return "Usa: Quitar <n>"

    # ---------------------------
    # CONFIRMAR PEDIDO
    # ---------------------------
    if text.lower() == "confirmar":
        u["state"] = "waiting_for_location"
        return "Envíame tu ubicación para calcular costo y distancia."

    # ---------------------------
    # ADMIN
    # ---------------------------
    if text.lower() == "admin process":
        created = delivery_manager.process_all_queues_and_create_tandas(carts.orders)
        return f"Tandas creadas: {created}"

    return "No entendido. Escribe 'Menu' para comenzar."


# -------------------------------------------------
#   MANEJO DE UBICACIÓN
# -------------------------------------------------
def handle_location_flow(phone, lat, lon):
    u = carts.get_user(phone)

    if u.get("state") == "waiting_for_location":
        order = carts.create_order_from_cart(phone, lat, lon)
        delivery_manager.enqueue_order(order)

        u["state"] = "idle"

        created = delivery_manager.process_all_queues_and_create_tandas(carts.orders)

        msg = (
            f"Pedido creado (ID {order['id']}). "
            f"Código: {order['code']}.\n"
            f"Distancia: {order.get('distance_km')} km.\n"
        )
        if created:
            msg += f"Tandas generadas: {created}"

        return msg

    return "Ubicación recibida."


# -------------------------------------------------
# INIT SERVER
# -------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
