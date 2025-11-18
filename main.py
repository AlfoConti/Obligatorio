# main.py
import os
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, JSONResponse
from algorithms.catalog_logic import send_product_menu, send_filter_menu, request_quantity
from utils.send_message import send_text_message
import uvicorn

from whatsapp_service import (
    send_whatsapp_buttons,
    send_whatsapp_text,
    send_whatsapp_list,
)

app = FastAPI()
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "token123")

# Simple in-memory sessions
SESSIONS = {}

def get_session(user):
    s = SESSIONS.get(user)
    if not s:
        s = {
            "page": 0,
            "category": "Todos",
            "sort": None,
            "cart": [],
            "_filtered_products_cache": None,
            "pending_product": None,
        }
        SESSIONS[user] = s
    return s


@app.get("/")
async def root():
    return {"status": "ok", "message": "Bot activo"}


# Meta Webhook Verification
@app.get("/whatsapp")
async def verify(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return PlainTextResponse(challenge)

    return PlainTextResponse("Verification failed", status_code=403)


# ============================================================
# WEBHOOK
# ============================================================
@app.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    body = await request.json()

    try:
        entry = body.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return JSONResponse({"status": "no_messages"})

        msg = messages[0]
        user = msg.get("from")
        session = get_session(user)

        # ----------------------------------------
        # INTERACTIVE (botones o listas)
        # ----------------------------------------
        if msg.get("type") == "interactive":
            inter = msg.get("interactive")
            itype = inter.get("type")

            if itype == "list_reply":
                row_id = inter["list_reply"]["id"]
                return await handle_list_reply(user, row_id)

            if itype == "button_reply":
                btn_id = inter["button_reply"]["id"]
                return await handle_button_reply(user, btn_id)

        # ----------------------------------------
        # TEXT MESSAGES
        # ----------------------------------------
        if msg.get("type") == "text":
            text = msg["text"]["body"].strip().lower()

            if text in ["menu", "hola", "inicio", "start"]:
                session["page"] = 0
                session["category"] = "Todos"
                session["sort"] = None

                # -----------------------------------
                # MENÚ INICIAL CON BOTONES
                # -----------------------------------
                buttons = [
                    {"id": "menu_products", "title": "Ver Productos"},
                    {"id": "menu_cart", "title": "Ver Carrito"},
                    {"id": "menu_help", "title": "Ayuda"},
                ]

                send_whatsapp_buttons(
                    user,
                    header="Bienvenido",
                    body="Elige una opción:",
                    buttons=buttons,
                )

                return JSONResponse({"status": "menu_sent"})

            send_text_message(user, "Escribe *menu* para comenzar.")
            return JSONResponse({"status": "text_ok"})

        send_text_message(user, "Mensaje no soportado. Usa *menu*.")
        return JSONResponse({"status": "unsupported"})

    except Exception as e:
        print("Webhook ERROR:", e)
        return JSONResponse({"status": "error", "detail": str(e)})


# ============================================================
# LIST REPLY (productos, filtros, sort, paginado)
# ============================================================
async def handle_list_reply(user, row_id):
    session = get_session(user)

    if row_id.startswith("prod_"):
        prod_id = row_id.replace("prod_", "")
        session["pending_product"] = prod_id
        request_quantity(user, prod_id)
        return JSONResponse({"status": "ask_qty"})

    if row_id == "ctl_filter":
        send_filter_menu(user)
        return JSONResponse({"status": "filter"})

    if row_id == "ctl_sort":
        if session["sort"] is None:
            session["sort"] = "asc"
        elif session["sort"] == "asc":
            session["sort"] = "desc"
        else:
            session["sort"] = None

        session["page"] = 0
        send_product_menu(user, session)
        return JSONResponse({"status": "sorted"})

    if row_id.startswith("ctl_next_"):
        session["page"] = int(row_id.split("ctl_next_", 1)[1])
        send_product_menu(user, session)
        return JSONResponse({"status": "next_page"})

    if row_id.startswith("ctl_prev_"):
        session["page"] = int(row_id.split("ctl_prev_", 1)[1])
        send_product_menu(user, session)
        return JSONResponse({"status": "prev_page"})

    if row_id.startswith("cat_"):
        session["category"] = row_id.replace("cat_", "")
        session["page"] = 0
        send_product_menu(user, session)
        return JSONResponse({"status": "category_set"})

    send_text_message(user, "Opción no reconocida.")
    return JSONResponse({"status": "unknown"})


# ============================================================
# BUTTON REPLY (cantidades + menú inicial)
# ============================================================
async def handle_button_reply(user, btn_id):
    session = get_session(user)

    # ---------------------------
    # CANTIDAD
    # ---------------------------
    if btn_id.startswith("qty_"):
        _, prod_id, qty = btn_id.split("_")
        qty = int(qty)

        session["cart"].append({"product_id": prod_id, "qty": qty})

        lines = [f"{x['product_id']} x{x['qty']}" for x in session["cart"]]
        send_text_message(user, "🛒 *Carrito:*\n" + "\n".join(lines))

        return JSONResponse({"status": "added_to_cart"})

    # ---------------------------
    # MENÚ PRINCIPAL
    # ---------------------------
    if btn_id == "menu_products":
        send_product_menu(user, session)
        return JSONResponse({"status": "open_products"})

    if btn_id == "menu_cart":
        if not session["cart"]:
            send_text_message(user, "Tu carrito está vacío.")
        else:
            lines = [f"{x['product_id']} x{x['qty']}" for x in session["cart"]]
            send_text_message(user, "🛒 *Carrito actual:*\n" + "\n".join(lines))
        return JSONResponse({"status": "cart_open"})

    if btn_id == "menu_help":
        send_text_message(user, "Usa *menu* para empezar.")
        return JSONResponse({"status": "help"})

    send_text_message(user, "Botón no reconocido.")
    return JSONResponse({"status": "unknown_button"})


# Run locally
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
