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
    send_edit_menu,
    send_edit_actions,
    send_cart,
    USERS,
    CART
)

from whatsapp_service import send_whatsapp_buttons, send_whatsapp_text, send_whatsapp_list

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

        # ----------------------------
        # INTERACTIVE
        # ----------------------------
        if msg.get("type") == "interactive":
            inter = msg["interactive"]

            # LISTAS
            if inter["type"] == "list_reply":
                row_id = inter["list_reply"]["id"]
                await handle_list_reply(user_number, row_id)
                return JSONResponse({"status": "ok"})

            # BOTONES
            if inter["type"] == "button_reply":
                btn_id = inter["button_reply"]["id"]
                await handle_button_reply(user_number, btn_id)
                return JSONResponse({"status": "ok"})

        # ----------------------------
        # TEXT
        # ----------------------------
        if msg.get("type") == "text":
            text = msg["text"]["body"].strip()
            txt = text.lower()

            # ESTADO: agregar nota
            if user.state == "adding_note":
                note_text = "" if txt == "no" else text
                save_cart_line(user_number, note_text)

                # limpiar estado
                user.state = "browsing"
                user.pending_qty = None
                user.pending_product_id = None

                send_whatsapp_text(user_number, "✔️ Producto agregado al carrito.")
                return JSONResponse({"status": "ok"})

            # comandos globales
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

            # fallback
            send_whatsapp_text(user_number, "No entendí 🤖. Escribe *menu* para comenzar.")
            return JSONResponse({"status": "ok"})

        # unsupported
        send_whatsapp_text(user_number, "Escribe *menu* para comenzar.")
        return JSONResponse({"status": "ok"})

    except Exception as e:
        print("❌ Error en webhook:", e)
        return JSONResponse({"status": "ok"})


# ==========================================================
# LIST HANDLER
# ==========================================================
async def handle_list_reply(user_number: str, row_id: str):
    user = get_user_obj(user_number)

    # selecciona producto
    if row_id.startswith("prod_"):
        prod_id = row_id.replace("prod_", "")
        USERS.set_pending_product(user_number, prod_id)
        USERS.set_state(user_number, "adding_qty")
        request_quantity(user_number, prod_id)
        return

    # abrir filtros
    if row_id == "ctl_filter":
        send_filter_menu(user_number)
        return

    # ordenar asc/desc/reset
    if row_id == "ctl_sort":
        user.sort = (
            "asc" if user.sort is None else
            "desc" if user.sort == "asc" else
            None
        )
        user.page = 0
        send_product_menu(user_number)
        return

    # paginación
    if row_id.startswith("ctl_next_"):
        user.page = int(row_id.replace("ctl_next_", ""))
        send_product_menu(user_number)
        return

    if row_id.startswith("ctl_prev_"):
        user.page = int(row_id.replace("ctl_prev_", ""))
        send_product_menu(user_number)
        return

    # categorías
    if row_id.startswith("cat_"):
        user.category = row_id.replace("cat_", "")
        user.page = 0
        send_product_menu(user_number)
        return

    # editar item en carrito (viene de send_edit_menu list)
    if row_id.startswith("edit_"):
        try:
            idx = int(row_id.replace("edit_", ""))
        except Exception:
            send_whatsapp_text(user_number, "Índice inválido.")
            return
        # mostrar acciones para ese item
        send_edit_actions(user_number, idx)
        return

    send_whatsapp_text(user_number, "Opción no reconocida.")


# ==========================================================
# BUTTON HANDLER
# ==========================================================
async def handle_button_reply(user_number: str, btn_id: str):
    user = get_user_obj(user_number)

    # abrir catálogo
    if btn_id == "btn_catalogo":
        USERS.reset_catalog_flow(user_number)
        send_product_menu(user_number)
        return

    # ver carrito (muestra botones dentro de send_cart)
    if btn_id == "btn_carrito":
        # use send_cart which returns buttons cart_edit/cart_clear
        send_cart(user_number)
        return

    # info
    if btn_id == "btn_info":
        send_whatsapp_text(user_number, "ℹ️ Somos una tienda online. ¿Qué necesitas?")
        return

    # cantidad seleccionada (nuevo producto)
    if btn_id.startswith("qty_"):
        try:
            _, prod_id, qty_s = btn_id.split("_")
            qty = int(qty_s)
        except Exception:
            send_whatsapp_text(user_number, "Formato de cantidad inválido.")
            return

        user.pending_qty = qty
        USERS.set_state(user_number, "adding_note")
        ask_for_note(user_number)
        return

    # === BOTONES DEL CARRITO ===
    if btn_id == "cart_edit":
        # abrir menú de edición (lista de items)
        send_edit_menu(user_number)
        return

    if btn_id == "cart_clear":
        # vaciar carrito
        CART.clear(user)
        send_whatsapp_text(user_number, "🗑 Tu carrito fue vaciado.")
        # opcional: mostrar carrito vacío
        send_cart(user_number)
        return

    # botones generados por send_edit_actions:
    # - edit_qty_{index}
    # - edit_rm_{index}
    # - edit_setqty_{index}_{n}  (cuando usuario elige nueva cantidad)
    if btn_id.startswith("edit_qty_"):
        # pedir nueva cantidad para el índice (mostramos botones 1..5)
        try:
            idx = int(btn_id.replace("edit_qty_", ""))
        except Exception:
            send_whatsapp_text(user_number, "Índice inválido.")
            return

        # validate index
        if not (0 <= idx < len(user.cart)):
            send_whatsapp_text(user_number, "Índice fuera de rango.")
            return

        # preparar botones para nueva cantidad (1..5)
        buttons = [
            {"id": f"edit_setqty_{idx}_1", "title": "1"},
            {"id": f"edit_setqty_{idx}_2", "title": "2"},
            {"id": f"edit_setqty_{idx}_3", "title": "3"},
            {"id": f"edit_setqty_{idx}_4", "title": "4"},
            {"id": f"edit_setqty_{idx}_5", "title": "5"},
        ]
        prod = user.cart[idx]["product"]
        return send_whatsapp_buttons(
            user_number,
            header=prod.get("nombre", prod.get("name", "Producto")),
            body="Selecciona la nueva cantidad:",
            buttons=buttons
        )

    if btn_id.startswith("edit_rm_"):
        # quitar item del carrito por índice
        try:
            idx = int(btn_id.replace("edit_rm_", ""))
        except Exception:
            send_whatsapp_text(user_number, "Índice inválido.")
            return

        if CART.remove(user, idx):
            send_whatsapp_text(user_number, "❌ Item eliminado del carrito.")
        else:
            send_whatsapp_text(user_number, "No se pudo eliminar (índice inválido).")

        # mostrar carrito actualizado
        send_cart(user_number)
        return

    if btn_id.startswith("edit_setqty_"):
        # aplicar nueva cantidad
        # formato: edit_setqty_{idx}_{n}
        try:
            parts = btn_id.split("_")
            idx = int(parts[2])
            new_qty = int(parts[3])
        except Exception:
            send_whatsapp_text(user_number, "Formato inválido para actualizar cantidad.")
            return

        if not (0 <= idx < len(user.cart)):
            send_whatsapp_text(user_number, "Índice fuera de rango.")
            return

        # obtener precio y recalcular subtotal
        item = user.cart[idx]
        prod = item["product"]
        # use CartManager helpers to compute price if present
        try:
            price = CART._get_product_price(prod)
        except Exception:
            # fallback: intentar claves directas
            price = float(prod.get("precio", prod.get("price", 0)) or 0)

        item["qty"] = int(new_qty)
        item["subtotal"] = round(price * int(new_qty), 2)

        send_whatsapp_text(user_number, "✅ Cantidad actualizada.")
        send_cart(user_number)
        return

    # fallback
    send_whatsapp_text(user_number, "Botón no reconocido.")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
