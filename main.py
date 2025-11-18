from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
import uvicorn
import os

from utils.send_message import send_whatsapp_message
from utils.get_type_message import get_type_message
from algorithms.catalog_logic import CatalogLogic
from algorithms.delivery_manager import DeliveryManager

app = FastAPI()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "pepito")  # tu token de Meta


# ---------------------------
# GET - TOKEN VERIFICATION
# ---------------------------
@app.get("/whatsapp")
async def verify_token(request: Request):
    params = request.query_params

    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == VERIFY_TOKEN:
        return PlainTextResponse(params.get("hub.challenge"))

    return PlainTextResponse("Verification failed", status_code=403)


# ---------------------------
# POST - RECEIVE MESSAGES
# ---------------------------
@app.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    body = await request.json()

    try:
        entry = body["entry"][0]["changes"][0]["value"]["messages"][0]
        message_type = get_type_message(entry)
        phone = entry["from"]

        # Ejemplo simple para testear
        if message_type == "text":
            text = entry["text"]["body"].lower()

            if "hola" in text:
                send_whatsapp_message("¡Hola! Soy tu bot 😄", phone)
            else:
                send_whatsapp_message(f"Recibí tu mensaje: {text}", phone)

        return JSONResponse({"status": "ok"}, status_code=200)

    except Exception as e:
        print("Error processing message:", e)
        return JSONResponse({"status": "ignored"}, status_code=200)


# ---------------------------
# ROOT
# ---------------------------
@app.get("/")
async def root():
    return {"message": "Bot WhatsApp Activo - FastAPI en Render"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3000)
