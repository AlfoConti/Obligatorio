# main.py (completo)
import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, JSONResponse

from algorithms.catalog_logic import (
    send_product_menu,
    send_filter_menu,
    request_quantity,
    ask_for_note,
    save_cart_line,
    find_product,
    USERS,
    CART,
    send_cart,
    send_edit_menu,
    send_edit_actions
)

from whatsapp_service import send_whatsapp_buttons, send_whatsapp_text

# Delivery manager
from algorithms.delivery_manager import DELIVERY_MANAGER

app = FastAPI()
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "token123")


def get_user_obj(number: str):
    return USERS.get(number)


# -------------------------------------------------
# Registrar deliveries de prueba (opcional)
# -------------------------------------------------
# Si quieres que los repartidores usen su teléfono como id,
# registralos aquí usando su número (ej: "+5989...").
# Puedes cambiar o eliminar estas líneas en producción.
try:
    if DELIVERY_MANAGER:
        # registros de ejemplo (cambia a los números reales si quieres)
        DELIVERY_MANAGER.register_delivery(os.environ.get("DELIVERY_1_ID", "delivery_1_phone"))
        DELIVERY_MANAGER.register_delivery(os.environ.get("DELIVERY_2_ID", "delivery_2_phone"))
except Exception as e:
    print("⚠️ Error registrando deliveries de prueba:", e)


# ==========================================================
# UNIVERSAL BUTTON ID EXTRACTOR (COMPATIBLE 2024–2025)
# ==========================================================
def get_button_id(msg):
    inter = msg.get("interactive", {})

    # WHATSAPP CLASSIC BUTTONS
    if "button_reply" in inter:
        return inter["button_reply"]["id"].strip()

    # NEW 2025 BUTTON FORMAT
    if inter.get("type") == "button" and "button_reply" in inter:
        return inter["button_reply"]["id"].strip()

    # TEMPLATE BUTTONS
    if "button" in msg:
        v = msg["button"].get("payload") or msg["button"].get("id")
        if v:
            return v.strip()

    return None


# ==========================================================
# UNIVERSAL LIST ID EXTRACTOR
# ==========================================================
def get_list_id(msg):
    inter = msg.get("interactive", {})
    if inter.get("type") == "list_reply":
        return inter["list_reply"]["id"].strip()
    return None


# ==========================================================
# ROOT
# ==========================================================
@app.get("/")
async def root():
    return {"status": "ok", "message": "Bot activo"}


@app.get("/whatsapp")
async def verify(request: Request):
    params = request.query_params
    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == VERIFY_TOKEN:
        return PlainTextResponse(params.get("hub.challenge"))
    return PlainTextResponse("Verification failed", status_code=403)


# ==========================================================
# MAIN WHATSAPP WEBHOOK
# ==========================================================
@app.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    try:
        body = await request.json()
        print("📥 WEBHOOK RECIBIDO:", body)

        entry = body.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return JSONResponse({"status": "ok"})

        msg = messages[0]
        user_number = msg.get("from")
        user = get_user_obj(user_number)

        # ========= LISTA =========
        row_id = get_list_id(msg)
        if row_id:
            handle_list_reply(user_number, row_id)
            return JSONResponse({"status": "ok"})

        # ========= BOTÓN =========
        btn_id = get_button_id(msg)
        if btn_id:
            print("🔘 Botón detectado:", btn_id)
            handle_button_reply(user_number, btn_id)
            return JSONResponse({"status": "ok"})

        # ========= UBICACIÓN =========
        if msg.get("type") == "location":
            # Si el usuario estaba esperando ubicación, creamos la orden y encolamos
            user = get_user_obj(user_number)
            if getattr(user, "state", None) != "awaiting_location":
                send_whatsapp_text(user_number, "No estoy esperando una ubicación ahora mismo. Escribe *menu* para comenzar.")
                return JSONResponse({"status": "ok"})

            loc = msg.get("location", {})
            lat = loc.get("latitude")
            lon = loc.get("longitude")
            if lat is None or lon is None:
                send_whatsapp_text(user_number, "No pude leer la ubicación. ¿Podés intentarlo de nuevo?")
                return JSONResponse({"status": "ok"})

            # Crear orden: usa CART.create_order(user, lat=..., lon=...) si tu CartManager soporta lat/lon
            try:
                # intenta con lat/lon si la implementación lo soporta
                order = CART.create_order(user, lat=lat, lon=lon)
            except TypeError:
                # fallback: create_order() sin lat/lon y luego asignar
                order = CART.create_order(user)
                order["lat"] = lat
                order["lon"] = lon

            if order is None:
                send_whatsapp_text(user_number, "No hay productos en tu carrito. Agrega algo antes de confirmar.")
                USERS.set_state(user_number, "browsing")
                return JSONResponse({"status": "ok"})

            # Encolar la orden en el Delivery Manager
            if DELIVERY_MANAGER is None:
                send_whatsapp_text(user_number, "El sistema de delivery no está disponible. Intentá más tarde.")
                USERS.set_state(user_number, "browsing")
                return JSONResponse({"status": "ok"})

            try:
                enqueued_order = DELIVERY_MANAGER.enqueue_order(order)
            except Exception as e:
                print("❌ ERROR en enqueue_order:", e)
                send_whatsapp_text(user_number, "Hubo un error al procesar tu pedido. Intentá nuevamente más tarde.")
                USERS.set_state(user_number, "browsing")
                return JSONResponse({"status": "ok"})

            # Enviar código al cliente
            send_whatsapp_text(user_number, f"✅ Pedido recibido. Tu código de entrega es *{enqueued_order.get('code')}*.\nTe avisaremos cuando el repartidor llegue.")
            USERS.set_state(user_number, "browsing")
            return JSONResponse({"status": "ok"})

        # ========= TEXTO =========
        if msg.get("type") == "text":
            text = msg["text"]["body"].strip().lower()

            # ——— Verificación de entrega por repartidor (ej: "entrego ABC123" o solo "ABC123") ———
            if text.startswith("entrego ") or (len(text) == 6 and text.isalnum()):
                parts = text.split()
                code = parts[1] if parts[0] == "entrego" and len(parts) > 1 else text.upper()
                # asumimos que el número del repartidor está registrado como delivery id
                delivery_id = user_number
                ok = False
                if DELIVERY_MANAGER:
                    ok = DELIVERY_MANAGER.verify_and_mark_delivered(delivery_id, code)
                if ok:
                    send_whatsapp_text(user_number, "Código verificado. Pedido marcado como entregado. Gracias.")
                else:
                    send_whatsapp_text(user_number, "Código inválido o no corresponde al pedido actual.")
                return JSONResponse({"status": "ok"})

            # ——— Usuario escribiendo nota ———
            if user.state == "adding_note":
                save_cart_line(user_number, "" if text == "no" else text)
                return JSONResponse({"status": "ok"})

            # ——— Comandos base ———
            if text in ["hola", "menu", "inicio", "start", "catalogo"]:
                USERS.reset_catalog_flow(user_number)
                send_whatsapp_buttons(
                    user_number,
                    header="Menú principal",
                    body="Selecciona una opción:",
                    buttons=[
                        {"id": "btn_catalogo", "title": "Ver catálogo"},
                        {"id": "btn_carrito", "title": "Ver carrito"},
                        {"id": "btn_info", "title": "Información"},
                    ],
                )
                return JSONResponse({"status": "ok"})

            send_whatsapp_text(user_number, "No entendí 🤖. Escribe *menu* para comenzar.")
            return JSONResponse({"status": "ok"})

        send_whatsapp_text(user_number, "Escribe *menu* para comenzar.")
        return JSONResponse({"status": "ok"})

    except Exception as e:
        print("❌ ERROR EN WEBHOOK:", e)
        return JSONResponse({"status": "ok"})


# ==========================================================
# HANDLER DE LISTAS
# ==========================================================
def handle_list_reply(user_number: str, row_id: str):
    user = get_user_obj(user_number)

    # Selección de producto
    if row_id.startswith("prod_"):
        prod_id = row_id.replace("prod_", "")
        request_quantity(user_number, prod_id)
        return

    # Filtro
    if row_id == "ctl_filter":
        send_filter_menu(user_number)
        return

    # Orden
    if row_id == "ctl_sort":
        user.sort = "asc" if user.sort is None else ("desc" if user.sort == "asc" else None)
        user.page = 0
        send_product_menu(user_number)
        return

    # Paginación
    if row_id.startswith("ctl_next_"):
        user.page = int(row_id.replace("ctl_next_", ""))
        send_product_menu(user_number)
        return

    if row_id.startswith("ctl_prev_"):
        user.page = int(row_id.replace("ctl_prev_", ""))
        send_product_menu(user_number)
        return

    # Categoría
    if row_id.startswith("cat_"):
        user.category = row_id.replace("cat_", "")
        user.page = 0
        send_product_menu(user_number)
        return

    # Editar → seleccionar ítem
    if row_id.startswith("edit_"):
        index = int(row_id.replace("edit_", ""))
        send_edit_actions(user_number, index)
        return

    send_whatsapp_text(user_number, "Opción no reconocida.")


# ==========================================================
# HANDLER DE BOTONES
# ==========================================================
def handle_button_reply(user_number: str, btn_id: str):
    user = get_user_obj(user_number)
    btn_id = btn_id.strip().lower()

    # ——— Catálogo ———
    if btn_id == "btn_catalogo":
        USERS.reset_catalog_flow(user_number)
        send_product_menu(user_number)
        return

    # ——— Carrito ———
    if btn_id == "btn_carrito":
        send_cart(user_number)
        return

    # ——— Información ———
    if btn_id == "btn_info":
        send_whatsapp_text(user_number, "ℹ️ Somos una tienda online. ¿Qué necesitas?")
        return

    # ——— Cantidad seleccionada ———
    if btn_id.startswith("qty_"):
        parts = btn_id.split("_")
        if len(parts) == 3:
            _, prod_id, qty_s = parts
            qty = int(qty_s)
            user.pending_qty = qty
            USERS.set_state(user_number, "adding_note")
            ask_for_note(user_number)
            return

        send_whatsapp_text(user_number, "Error leyendo la cantidad.")
        return

    # ——— Carrito: agregar más ———
    if btn_id == "cart_add_more":
        USERS.reset_catalog_flow(user_number)
        send_product_menu(user_number)
        return

    # ——— Carrito: finalizar ———
    if btn_id == "cart_finish":
        # solicitamos ubicación al usuario antes de crear la orden
        USERS.set_state(user_number, "awaiting_location")
        send_whatsapp_text(
            user_number,
            "Perfecto ✅. Para confirmar el pedido por favor *comparte tu ubicación* usando el botón de Adjuntar → Ubicación.\n"
            "Si no podes, envía tu dirección en texto (calle y número)."
        )
        return

    # ——— Carrito: editar ———
    if btn_id == "cart_edit":
        send_edit_menu(user_number)
        return

    # ——— Vaciar carrito ———
    if btn_id == "cart_clear":
        CART.clear(user)
        send_whatsapp_text(user_number, "🗑 Carrito vaciado.")
        return

    # ——— Editar → cantidad ———
    if btn_id.startswith("edit_qty_"):
        idx = int(btn_id.replace("edit_qty_", ""))
        item = user.cart[idx]
        request_quantity(user_number, item["product"]["id"])
        return

    # ——— Editar → eliminar ———
    if btn_id.startswith("edit_rm_"):
        idx = int(btn_id.replace("edit_rm_", ""))
        CART.remove(user, idx)
        send_cart(user_number)
        return

    send_whatsapp_text(user_number, "Botón no reconocido.")


# ==========================================================
# RUN
# ==========================================================
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
