# main.py
import os
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, JSONResponse
from algorithms.catalog_logic import send_product_menu, send_filter_menu, request_quantity

# alias para mantener compatibilidad con tu código
from utils.send_message import send_whatsapp_message as send_text_message

# funciones interactivas (buttons / list) en whatsapp_service.py
from whatsapp_service import send_whatsapp_buttons, send_whatsapp_text, send_whatsapp_list

import uvicorn

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


# Root
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


# Webhook Listener
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
        # INTERACTIVE BUTTONS / LIST RESPONSES
        # ----------------------------------------
        if msg.get("type") == "interactive":
            inter = msg.get("interactive", {})
            itype = inter.get("type")

            # LIST REPLY (product list, filter, pages)
            if itype == "list_reply":
                lr = inter.get("list_reply", {})
                row_id = lr.get("id")
                return await handle_list_reply(user, row_id)

            # BUTTON REPLY (quantities, menu actions)
            elif itype == "button_reply":
                br = inter.get("button_reply", {})
                btn_id = br.get("id")
                return await handle_button_reply(user, btn_id)

        # ----------------------------------------
        # TEXT MESSAGES
        # ----------------------------------------
        if msg.get("type") == "text":
            body_text = msg.get("text", {}).get("body", "").strip().lower()

            # PALABRAS QUE ABREN EL MENÚ PRINCIPAL
            if body_text in ["menu", "hola", "inicio", "start"]:
                session["page"] = 0
                session["category"] = "Todos"
                session["sort"] = None

                # ENVÍO DE BOTONES (usar la firma: number, header, body, buttons)
                send_whatsapp_buttons(
                    user,
                    header="Menú principal",
                    body="Selecciona una opción:",
                    buttons=[
                        {"id": "menu_products", "title": "📦 Ver Productos"},
                        {"id": "menu_cart", "title": "🛒 Ver Carrito"},
                        {"id": "menu_help", "title": "❓ Ayuda"},
                    ],
                )

                return JSONResponse({"status": "buttons_sent"})

            # Si no es trigger de menú, sugerimos usar 'menu'
            send_text_message(user, "Escribe *menu* para ver las opciones.")
            return JSONResponse({"status": "text_handled"})

        # Tipo no soportado
        send_text_message(user, "Tipo de mensaje no soportado. Usa *menu*.")
        return JSONResponse({"status": "unsupported"})

    except Exception as e:
        print("Webhook error:", e)
        return JSONResponse({"status": "error", "detail": str(e)})


# =====================================================
# LIST REPLY HANDLER
# =====================================================
async def handle_list_reply(user, row_id):
    session = get_session(user)

    if row_id.startswith("prod_"):
        prod_id = row_id.replace("prod_", "")
        session["pending_product"] = prod_id
        request_quantity(user, prod_id)
        return JSONResponse({"status": "asked_qty"})

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
        session["page"] = int(row_id.replace("ctl_next_", ""))
        send_product_menu(user, session)
        return JSONResponse({"status": "next"})

    if row_id.startswith("ctl_prev_"):
        session["page"] = int(row_id.replace("ctl_prev_", ""))
        send_product_menu(user, session)
        return JSONResponse({"status": "prev"})

    if row_id.startswith("cat_"):
        cat = row_id.replace("cat_", "")
        session["category"] = cat
        session["page"] = 0
        send_product_menu(user, session)
        return JSONResponse({"status": "category"})

    send_text_message(user, "Opción no reconocida.")
    return JSONResponse({"status": "unknown"})


# =====================================================
# BUTTON REPLY HANDLER
# =====================================================
async def handle_button_reply(user, btn_id):
    session = get_session(user)

    # qty pattern: qty_PRODUCTO_3
    if btn_id.startswith("qty_"):
        _, prod_id, qty = btn_id.split("_")
        qty = int(qty)
        session["cart"].append({"product_id": prod_id, "qty": qty})
        lines = [f"{item['product_id']} x{item['qty']}" for item in session["cart"]]
        send_text_message(user, "🛒 *Carrito actual:*\n" + "\n".join(lines))
        return JSONResponse({"status": "added"})

    # menu buttons
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
