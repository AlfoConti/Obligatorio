from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

from utils.get_type_message import get_message_type
from utils.send_message import send_whatsapp_message

from algorithms.catalog_logic import CatalogManager
from utils.cart_management import CartManager
from utils.geo_calculator import GeoCalculator

app = FastAPI()

catalog = CatalogManager()
cart = CartManager()


@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    data = await request.json()

    msg_type = get_message_type(data)
    number = data["entry"][0]["changes"][0]["value"]["messages"][0]["from"]

    if msg_type == "text":
        user_text = data["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"]

        # ejemplo básico
        if user_text.lower() == "hola":
            send_whatsapp_message(number, "¡Hola! ¿Qué deseas pedir hoy?")
            return JSONResponse({"status": "ok"})

        return JSONResponse({"status": "ok"})

    elif msg_type == "location":
        loc = data["entry"][0]["changes"][0]["value"]["messages"][0]["location"]
        lat = loc["latitude"]
        lng = loc["longitude"]

        send_whatsapp_message(number, f"Ubicación recibida\nLat: {lat}\nLng: {lng}")

        return JSONResponse({"status": "ok"})

    return JSONResponse({"status": "ignored"})


@app.get("/")
def home():
    return {"status": "running"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
