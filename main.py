# main.py
import os
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, JSONResponse
from algorithms.catalog_logic import send_product_menu, send_filter_menu, request_quantity
from utils.send_message import send_text_message
import uvicorn

app = FastAPI()
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "token123")

# Simple in-memory sessions
SESSIONS = {}

def get_session(user):
    s = SESSIONS.get(user)
    if not s:
        s = {"page": 0, "category": "Todos", "sort": None, "cart": [], "_filtered_products_cache": None}
        SESSIONS[user] = s
    return s

@app.get("/")
async def root():
    return {"status": "ok", "message": "Bot activo"}

# Webhook verification endpoint (Meta expects this)
@app.get("/whatsapp")
async def verify(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return PlainTextResponse(challenge)
    return PlainTextResponse("Verification failed", status_code=403)

# Webhook listener
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

        # Interactive message
        if msg.get("type") == "interactive":
            inter = msg.get("interactive", {})
            itype = inter.get("type")
            if itype == "list_reply":
                lr = inter.get("list_reply", {})
                row_id = lr.get("id")
                return await handle_list_reply(user, row_id)
            elif itype == "button_reply":
                br = inter.get("button_reply", {})
                btn_id = br.get("id")
                return await handle_button_reply(user, btn_id)

        # Text message
        if msg.get("type") == "text":
            body_text = msg.get("text", {}).get("body", "").strip().lower()
            # initial menu trigger
            if body_text in ["menu", "hola", "start", "inicio"]:
                # send initial buttons
                send_text_message(user, "Bienvenido! Escribe 'menu' o pulsa el botón para ver productos.")
                # open first page
                session["page"] = 0
                session["category"] = "Todos"
                session["sort"] = None
                send_product_menu(user, session)
                return JSONResponse({"status": "menu_sent"})
            else:
                send_text_message(user, "Escribe 'menu' para ver el catálogo.")
                return JSONResponse({"status": "text_handled"})

        # Location, voice, etc - not handled here
        send_text_message(user, "Tipo de mensaje no soportado por el prototipo (usa 'menu').")
        return JSONResponse({"status": "unsupported_type"})

    except Exception as e:
        print("Webhook error:", e)
        return JSONResponse({"status": "error", "detail": str(e)})

# Handlers
async def handle_list_reply(user, row_id):
    session = get_session(user)
    # product row selected
    if row_id.startswith("prod_"):
        prod_id = row_id.split("prod_",1)[1]
        # ask for quantity via buttons
        request_quantity(user, prod_id)
        # store pending selection
        session["pending_product"] = prod_id
        return JSONResponse({"status": "asked_qty"})
    # control rows
    if row_id == "ctl_filter":
        send_filter_menu(user)
        return JSONResponse({"status": "filter_sent"})
    if row_id == "ctl_sort":
        # toggle sort: None -> asc -> desc -> None
        if session.get("sort") is None:
            session["sort"] = "asc"
        elif session["sort"] == "asc":
            session["sort"] = "desc"
        else:
            session["sort"] = None
        # reset page to 0 and resend menu
        session["page"] = 0
        send_product_menu(user, session)
        return JSONResponse({"status": "sorted"})
    if row_id.startswith("ctl_next_"):
        # pattern ctl_next_{page}
        new_page = int(row_id.split("ctl_next_",1)[1])
        session["page"] = new_page
        send_product_menu(user, session)
        return JSONResponse({"status": "next_page"})
    if row_id.startswith("ctl_prev_"):
        new_page = int(row_id.split("ctl_prev_",1)[1])
        session["page"] = new_page
        send_product_menu(user, session)
        return JSONResponse({"status": "prev_page"})
    if row_id == "ctl_start":
        session["page"] = 0
        send_product_menu(user, session)
        return JSONResponse({"status": "start_page"})
    if row_id.startswith("cat_"):
        cat = row_id.split("cat_",1)[1]
        session["category"] = cat
        session["page"] = 0
        send_product_menu(user, session)
        return JSONResponse({"status": "category_set"})
    # fallback
    send_text_message(user, "Opción no reconocida.")
    return JSONResponse({"status": "unknown_list"})

async def handle_button_reply(user, btn_id):
    session = get_session(user)
    # quantity selection pattern qty_{prodid}_{n}
    if btn_id.startswith("qty_"):
        _, prod_id, qty = btn_id.split("_",2)
        qty = int(qty)
        # add to cart (store minimal info: prod id and qty)
        session["cart"].append({"product_id": prod_id, "qty": qty})
        # show cart summary
        # We'll just show a simple text list for now
        lines = []
        for it in session["cart"]:
            lines.append(f"{it['product_id']} x{it['qty']}")
        lines.append("Opciones: Quitar / Seguir pidiendo / Confirmar")
        send_text_message(user, "Carrito:\n" + "\n".join(lines))
        return JSONResponse({"status": "added_to_cart"})
    # other button ids can be handled later
    send_text_message(user, "Botón no reconocido.")
    return JSONResponse({"status": "unknown_button"})

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
