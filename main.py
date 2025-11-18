# main.py
import os
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, JSONResponse

from algorithms.catalog_logic import send_product_menu, send_filter_menu, request_quantity
from utils.send_message import send_whatsapp_message as send_text_message
from whatsapp_service import send_whatsapp_buttons, send_whatsapp_text

import uvicorn

app = FastAPI()
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "token123")

# ----------------------------------------
# SESIONES EN MEMORIA
# ----------------------------------------
SESSIONS = {}

def get_session(user):
    if user not in SESSIONS:
        SESSIONS[user] = {
            "page": 0,
            "category": "Todos",
            "sort": None,
            "cart": [],
            "_filtered_products_cache": None,
            "pending_product": None
        }
    return SESSIONS[user]


# ----------------------------------------
# ROOT
# ----------------------------------------
@app.get("/")
async def root():
    return {"status": "ok", "message": "Bot activo"}


# ----------------------------------------
# VERIFICACIÓN DE META
# ----------------------------------------
@app.get("/whatsapp")
async def verify(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return PlainTextResponse(challenge)

    return PlainTextResponse("Verification failed", status_code=403)


# ----------------------------------------
# 📌 WEBHOOK POST — COMPLETAMENTE REEMPLAZADO
# ----------------------------------------
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
            return JSONResponse({"status": "no_messages"})

        msg = messages[0]
        user = msg.get("from")
        session = get_session(user)

        # ------------------------------------------------
        # INTERACTIVE (botones o listas)
        # ------------------------------------------------
        if msg.get("type") == "interactive":
            inter = msg.get("interactive", {})
            itype = inter.get("type")

            if itype == "list_reply":
                row_id = inter["list_reply"]["id"]
                return await handle_list_reply(user, row_id)

            if itype == "button_reply":
                btn_id = inter["button_reply"]["id"]
                return await handle_button_reply(user, btn_id)

        # ------------------------------------------------
        # TEXTO
        # ------------------------------------------------
        if msg.get("type") == "text":
            body_text = msg.get("text", {}).get("body", "").lower().strip()

            if body_text in ["hola", "menu", "inicio", "start"]:
                send_whatsapp_buttons(
                    user,
                    header="Menú principal",
                    body="Selecciona una opción:",
                    buttons=[
                        {"id": "btn_catalogo", "title": "Ver catálogo"},
                        {"id": "btn_carrito", "title": "Ver carrito"},
                        {"id": "btn_info", "title": "Información"}
                    ]
                )
                return JSONResponse({"status": "menu_sent"})

            # Si escribe otra cosa
            send_text_message(user, "No entendí. Escribe *menu* para comenzar.")
            return JSONResponse({"status": "unknown_text"})

        # ------------------------------------------------
        # OTROS TIPOS NO MANEJADOS
        # ------------------------------------------------
        send_text_message(user, "Escribe *menu* para comenzar.")
        return JSONResponse({"status": "unsupported_type"})

    except Exception as e:
        print("Webhook error:", e)
        return JSONResponse({"status": "error", "detail": str(e)})


# ----------------------------------------
# HANDLER LISTAS
# ----------------------------------------
async def handle_list_reply(user, row_id):
    session = get_session(user)

    if row_id.startswith("prod_"):
        prod_id = row_id.replace("prod_", "")
        session["pending_product"] = prod_id
        request_quantity(user, prod_id)
        return JSONResponse({"status": "asking_qty"})

    if row_id == "ctl_filter":
        send_filter_menu(user)
        return JSONResponse({"status": "filter"})

    if row_id == "ctl_sort":
        session["sort"] = (
            "asc" if session["sort"] is None else
            "desc" if session["sort"] == "asc" else
            None
        )
        send_product_menu(user, session)
        return JSONResponse({"status": "sorted"})

    if row_id.startswith("ctl_next_"):
        session["page"] = int(row_id.replace("ctl_next_", ""))
        send_product_menu(user, session)
        return JSONResponse({"status": "next_page"})

    if row_id.startswith("ctl_prev_"):
        session["page"] = int(row_id.replace("ctl_prev_", ""))
        send_product_menu(user, session)
        return JSONResponse({"status": "prev_page"})

    if row_id.startswith("cat_"):
        session["category"] = row_id.replace("cat_", "")
        session["page"] = 0
        send_product_menu(user, session)
        return JSONResponse({"status": "category"})

    send_text_message(user, "Opción no reconocida.")
    return JSONResponse({"status": "unknown_list"})


# ----------------------------------------
# HANDLER BOTONES
# ----------------------------------------
async def handle_button_reply(user, btn_id):
    session = get_session(user)

    if btn_id.startswith("qty_"):
        _, prod_id, qty = btn_id.split("_")
        qty = int(qty)

        session["cart"].append({"product_id": prod_id, "qty": qty})

        cart_lines = "\n".join(
            f"{item['product_id']} x{item['qty']}" for item in session["cart"]
        )
        send_text_message(user, f"🛒 *Carrito actualizado:*\n{cart_lines}")

        return JSONResponse({"status": "qty_added"})

    send_text_message(user, "Botón no reconocido.")
    return JSONResponse({"status": "unknown_button"})


# ----------------------------------------
# LOCAL RUN
# ----------------------------------------
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
