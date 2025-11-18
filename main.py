# main.py
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


@app.get("/")
async def root():
    return {"status": "ok", "message": "Bot activo"}


@app.get("/whatsapp")
async def verify(request: Request):
    params = request.query_params
    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == VERIFY_TOKEN:
        return PlainTextResponse(params.get("hub.challenge"))
    return PlainTextResponse("Verification failed", status_code=403)


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

        # ================================
        # INTERACTIVE RESPONSES
        # ================================
        if msg.get("type") == "interactive":
            inter = msg["interactive"]

            # LIST MESSAGE
            if inter["type"] == "list_reply":
                row_id = inter["list_reply"]["id"]
                handle_list_reply(user_number, row_id)
                return JSONResponse({"status": "ok"})

            # BUTTON MESSAGE (API actual)
            if inter["type"] == "button":
                btn_id = inter["button_reply"]["id"]
                handle_button_reply(user_number, btn_id)
                return JSONResponse({"status": "ok"})

        # ================================
        # TEXT MESSAGE
        # ================================
        if msg.get("type") == "text":
            text = msg["text"]["body"].strip()
            txt = text.lower()

            # Estado: agregar nota
            if user.state == "adding_note":
                note_text = "" if txt == "no" else text
                save_cart_line(user_number, note_text)

                # limpiar estado
                user.state = "browsing"
                user.pending_qty = None
                user.pending_product_id = None

                send_whatsapp_text(user_number, "✔️ Producto agregado al carrito.")
                return JSONResponse({"status": "ok"})

            # Comandos globales
            if txt in ["hola", "menu", "inicio", "start", "catalogo"]:
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
        print("❌ Error en webhook:", e)
        return JSONResponse({"status": "ok"})


# ==========================================================
# LIST HANDLER
# ==========================================================
def handle_list_reply(user_number: str, row_id: str):
    user = get_user_obj(user_number)

    # Producto seleccionado
    if row_id.startswith("prod_"):
        prod_id = row_id.replace("prod_", "")
        USERS.set_pending_product(user_number, prod_id)
        USERS.set_state(user_number, "adding_qty")
        request_quantity(user_number, prod_id)
        return

    # Filtro
    if row_id == "ctl_filter":
        send_filter_menu(user_number)
        return

    # Orden
    if row_id == "ctl_sort":
        user.sort = (
            "asc" if user.sort is None else
            "desc" if user.sort == "asc" else
            None
        )
        user.page = 0
        send_product_menu(user_number)
        return

    # Paginación siguiente
    if row_id.startswith("ctl_next_"):
        user.page = int(row_id.replace("ctl_next_", ""))
        send_product_menu(user_number)
        return

    # Paginación anterior
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

    # Editar carrito → elegir item
    if row_id.startswith("edit_"):
        index = int(row_id.replace("edit_", ""))
        send_edit_actions(user_number, index)
        return

    send_whatsapp_text(user_number, "Opción no reconocida.")


# ==========================================================
# BUTTON HANDLER
# ==========================================================
def handle_button_reply(user_number: str, btn_id: str):
    user = get_user_obj(user_number)

    # Ver catálogo
    if btn_id == "btn_catalogo":
        USERS.reset_catalog_flow(user_number)
        send_product_menu(user_number)
        return

    # Ver carrito
    if btn_id == "btn_carrito":
        send_cart(user_number)
        return

    # Información
    if btn_id == "btn_info":
        send_whatsapp_text(user_number, "ℹ️ Somos una tienda online. ¿Qué necesitas?")
        return

    # Cantidad seleccionada
    if btn_id.startswith("qty_"):
        _, prod_id, qty_s = btn_id.split("_")
        qty = int(qty_s)
        user.pending_qty = qty
        USERS.set_state(user_number, "adding_note")
        ask_for_note(user_number)
        return

    # Carrito → Agregar más
    if btn_id == "cart_add_more":
        USERS.reset_catalog_flow(user_number)
        send_product_menu(user_number)
        return

    # Carrito → Finalizar
    if btn_id == "cart_finish":
        send_whatsapp_text(
            user_number,
            "🛍 Tu pedido fue recibido.\nEn breve nos comunicamos contigo."
        )
        return

    # Carrito → Editar
    if btn_id == "cart_edit":
        send_edit_menu(user_number)
        return

    # Carrito → Vaciar (opcional)
    if btn_id == "cart_clear":
        CART.clear(user)
        send_whatsapp_text(user_number, "🗑 Tu carrito ha sido vaciado.")
        return

    # Editar → Cambiar cantidad
    if btn_id.startswith("edit_qty_"):
        idx = int(btn_id.replace("edit_qty_", ""))
        item = user.cart[idx]
        prod = item["product"]
        request_quantity(user_number, prod["id"])
        return

    # Editar → Eliminar
    if btn_id.startswith("edit_rm_"):
        idx = int(btn_id.replace("edit_rm_", ""))
        CART.remove(user, idx)
        send_cart(user_number)
        return

    send_whatsapp_text(user_number, "Botón no reconocido.")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
