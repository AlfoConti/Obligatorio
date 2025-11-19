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

app = FastAPI()
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "token123")


def get_user_obj(number: str):
    return USERS.get(number)

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

        # ========= TEXTO =========
        if msg.get("type") == "text":
            text = msg["text"]["body"].strip().lower()

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
        send_whatsapp_text(user_number, "🛍 Tu pedido fue recibido. En breve nos comunicamos contigo.")
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
