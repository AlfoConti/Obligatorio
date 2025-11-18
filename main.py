# main.py
import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, JSONResponse

# funciones de catálogo (usan USERS y CART internamente)
from algorithms.catalog_logic import (
    send_product_menu,
    send_filter_menu,
    request_quantity,
    ask_for_note,
    save_cart_line,
    find_product,
    USERS,   # gestor de usuarios (UserManager)
    CART     # gestor de carrito (CartManager)
)

# funciones de envío (whatsapp)
from whatsapp_service import send_whatsapp_buttons, send_whatsapp_text

app = FastAPI()
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "token123")


# ---------------------------
# Helpers
# ---------------------------
def get_user_obj(number: str):
    """Devuelve el objeto User (gestor USERS)."""
    return USERS.get(number)


# ---------------------------
# Root & Verification (Meta)
# ---------------------------
@app.get("/")
async def root():
    return {"status": "ok", "message": "Bot activo"}


@app.get("/whatsapp")
async def verify(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return PlainTextResponse(challenge)

    return PlainTextResponse("Verification failed", status_code=403)


# ---------------------------
# Webhook receiver
# ---------------------------
@app.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    try:
        body = await request.json()
        print("📥 WEBHOOK RECIBIDO:", body)

        entry = body.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        # nothing to do
        if not messages:
            return JSONResponse({"status": "no_messages"})

        msg = messages[0]
        user_number = msg.get("from")
        user = get_user_obj(user_number)

        # -----------------------
        # Interactive messages
        # -----------------------
        if msg.get("type") == "interactive":
            inter = msg.get("interactive", {})
            itype = inter.get("type")

            if itype == "list_reply":
                row_id = inter["list_reply"]["id"]
                return await handle_list_reply(user_number, row_id)

            if itype == "button_reply":
                btn_id = inter["button_reply"]["id"]
                return await handle_button_reply(user_number, btn_id)

        # -----------------------
        # Text messages
        # -----------------------
        if msg.get("type") == "text":
            text = msg.get("text", {}).get("body", "").strip()

            # If user is in 'adding_note' state, capture the note
            if user.state == "adding_note":
                note_text = text.strip()
                if note_text.lower() == "no":
                    note_text = ""
                # save the cart line (this function uses USERS and CART)
                resp = save_cart_line(user_number, note_text)
                # save_cart_line already sends a message with the cart via send_whatsapp_text.
                return JSONResponse({"status": "note_saved"})

            # If user is in other special states you may handle here (e.g., waiting_location)
            # For now, fallback to main commands:
            txt_low = text.lower()
            if txt_low in ["hola", "menu", "inicio", "start", "catalogo"]:
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
                # reset catalog navigation state
                USERS.reset_catalog_flow(user_number)
                return JSONResponse({"status": "menu_sent"})

            # fallback message
            send_whatsapp_text(user_number, "No entendí 🤖. Escribe *menu* para comenzar.")
            return JSONResponse({"status": "unknown_text"})

        # If unhandled type
        send_whatsapp_text(user_number, "Escribe *menu* para comenzar.")
        return JSONResponse({"status": "unsupported_type"})

    except Exception as e:
        print("❌ Error en webhook:", e)
        return JSONResponse({"status": "error", "detail": str(e)})


# ---------------------------
# List reply handler
# ---------------------------
async def handle_list_reply(user_number: str, row_id: str):
    user = get_user_obj(user_number)

    # Producto seleccionado -> pedir cantidad (botones)
    if row_id.startswith("prod_"):
        prod_id = row_id.replace("prod_", "")
        USERS.set_pending_product(user_number, prod_id)
        USERS.set_state(user_number, "adding_qty")
        return request_quantity(user_number, prod_id)

    # Filtrar -> mostrar menú de filtros
    if row_id == "ctl_filter":
        return send_filter_menu(user_number)

    # Ordenar -> toggle asc/desc/none
    if row_id == "ctl_sort":
        new_sort = "asc" if user.sort is None else ("desc" if user.sort == "asc" else None)
        USERS.set_state(user_number, "browsing")
        user.sort = new_sort
        # reset page to 0 when changing sort
        user.page = 0
        return send_product_menu(user_number)

    # Paginación siguiente
    if row_id.startswith("ctl_next_"):
        page = int(row_id.replace("ctl_next_", ""))
        user.page = page
        return send_product_menu(user_number)

    # Paginación anterior
    if row_id.startswith("ctl_prev_"):
        page = int(row_id.replace("ctl_prev_", ""))
        user.page = page
        return send_product_menu(user_number)

    # Categoría seleccionada
    if row_id.startswith("cat_"):
        cat = row_id.replace("cat_", "")
        user.category = cat
        user.page = 0
        return send_product_menu(user_number)

    send_whatsapp_text(user_number, "Opción no reconocida.")
    return JSONResponse({"status": "unknown_list"})


# ---------------------------
# Button reply handler
# ---------------------------
async def handle_button_reply(user_number: str, btn_id: str):
    user = get_user_obj(user_number)

    # Mostrar catálogo
    if btn_id == "btn_catalogo":
        USERS.reset_catalog_flow(user_number)
        return send_product_menu(user_number)

    # Ver carrito
    if btn_id == "btn_carrito":
        cart_text = CART.format(user)
        return send_whatsapp_text(user_number, cart_text)

    # Información
    if btn_id == "btn_info":
        return send_whatsapp_text(user_number, "ℹ️ Somos una tienda online. ¿Qué necesitas?")

    # Botones de cantidad: cuando usuario presiona qty_PRODUCTO_N
    if btn_id.startswith("qty_"):
        try:
            _, prod_id, qty_s = btn_id.split("_")
            qty = int(qty_s)
        except Exception:
            return send_whatsapp_text(user_number, "Formato de cantidad inválido.")

        # store pending qty and ask for note
        USERS.get(user_number).pending_qty = qty
        USERS.set_state(user_number, "adding_note")

        # ask for optional note
        return ask_for_note(user_number)

    # fallback
    return send_whatsapp_text(user_number, "Botón no reconocido.")


# ---------------------------
# Local run
# ---------------------------
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
