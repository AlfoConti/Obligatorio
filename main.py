import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from utils.send_message import send_whatsapp_message
from utils.get_type_message import get_message_type
from utils.cart_management import (
    add_to_cart, view_cart, confirm_purchase,
    cancel_purchase
)
from algorithms.catalog_logic import get_catalog
from algorithms.geo_calculator import get_user_location
from algorithms.delivery_manager import get_nearest_delivery

# ============================
#  CONFIG
# ============================

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "testtoken")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")

if not WHATSAPP_PHONE_ID or not WHATSAPP_ACCESS_TOKEN:
    print("\n⚠ ADVERTENCIA: Variables de entorno de WhatsApp no configuradas.")
    print("   La app NO enviará mensajes hasta configurarlas en Render.\n")

app = FastAPI()


# ============================
#        WEBHOOK VERIFY
# ============================

@app.get("/webhook")
async def verify(request: Request):
    mode = request.query_params.get("hub.mode")
    challenge = request.query_params.get("hub.challenge")
    token = request.query_params.get("hub.verify_token")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return int(challenge)

    return JSONResponse(status_code=403, content="Verification failed")


# ============================
#        WEBHOOK POST
# ============================

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()

    try:
        entry = data["entry"][0]["changes"][0]["value"]
    except Exception:
        return {"status": "no_whatsapp_event"}

    if "messages" not in entry:
        return {"status": "ignored_no_messages"}

    message = entry["messages"][0]
    phone_number = entry["metadata"]["phone_number_id"]
    from_number = message["from"]

    message_type, content = get_message_type(message)

    print("\n===== NUEVO MENSAJE =====")
    print("Tipo:", message_type)
    print("Contenido:", content)

    # ======================================================
    #               MANEJO DE BOTONES (POSTBACK)
    # ======================================================

    if message_type == "button":
        button_id = content

        if button_id == "CATALOGO":
            catalog = get_catalog()
            send_whatsapp_message(from_number, catalog)

        elif button_id == "VER_CARRITO":
            msg = view_cart(from_number)
            send_whatsapp_message(from_number, msg)

        elif button_id == "CONFIRMAR":
            msg = confirm_purchase(from_number)
            send_whatsapp_message(from_number, msg)

        elif button_id == "CANCELAR":
            msg = cancel_purchase(from_number)
            send_whatsapp_message(from_number, msg)

        elif button_id == "LOCACION":
            msg = get_user_location(from_number)
            send_whatsapp_message(from_number, msg)

        elif button_id == "DELIVERY":
            msg = get_nearest_delivery(from_number)
            send_whatsapp_message(from_number, msg)

        elif button_id == "AYUDA":
            send_whatsapp_message(from_number, "📌 *Ayuda disponible*\nElegí una opción del menú.")

        return {"status": "button_processed"}

    # ======================================================
    #               MANEJO DE TEXTO NORMAL
    # ======================================================

    if message_type == "text":

        text = content.lower()

        # ------- PALABRAS QUE ABREN EL MENÚ -------
        if text in ["hola", "menu", "inicio", "ayuda"]:
            send_menu(from_number)
            return {"status": "menu_sent"}

        # ------- AGREGAR AL CARRITO -------
        if text.startswith("agregar "):
            item = text.replace("agregar ", "")
            msg = add_to_cart(from_number, item)
            send_whatsapp_message(from_number, msg)
            return {"status": "item_added"}

        # Si no matchea nada:
        send_whatsapp_message(from_number, "No entendí. Escribí *menu* para ver opciones.")
        return {"status": "unknown_text"}

    return {"status": "unhandled"}


# ============================
#       FUNCIÓN MENÚ
# ============================

def send_menu(to_number: str):
    """
    Envía los 7 botones principales (tus imágenes exactas).
    """

    text = "📋 *Menú principal*\nElegí una opción:"

    buttons = [
        {"id": "CATALOGO", "title": "📦 Catálogo"},
        {"id": "VER_CARRITO", "title": "🛒 Ver carrito"},
        {"id": "CONFIRMAR", "title": "✅ Confirmar compra"},
        {"id": "CANCELAR", "title": "❌ Cancelar compra"},
        {"id": "LOCACION", "title": "📍 Mi ubicación"},
        {"id": "DELIVERY", "title": "🚚 Delivery más cercano"},
        {"id": "AYUDA", "title": "❓ Ayuda"}
    ]

    send_whatsapp_message(to_number, text, buttons=buttons)


# ============================
#       SERVIDOR RENDER
# ============================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
