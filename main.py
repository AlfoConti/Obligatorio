from fastapi import FastAPI, Request
import requests
import os

app = FastAPI()

# 🔧 Variables de entorno (deben estar configuradas en Render)
WHATSAPP_URL = os.getenv("WHATSAPP_URL")  # Ej: https://graph.facebook.com/v19.0/<PHONE_NUMBER_ID>/messages
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")  # Token de acceso de tu app de Meta

# 🔹 Ruta raíz para comprobar que el servidor está vivo
@app.get("/")
def home():
    return {"status": "ok", "message": "Bot de WhatsApp activo"}

# 🔹 Endpoint que Meta usa para verificar el webhook
@app.get("/webhook")
def verify_webhook(request: Request):
    verify_token = os.getenv("VERIFY_TOKEN", "default_token")
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == verify_token:
            print("✅ Webhook verificado correctamente.")
            return int(challenge)
        else:
            print("❌ Verificación fallida.")
            return {"error": "Verificación fallida"}
    return {"error": "Parámetros inválidos"}

# 🔹 Endpoint que recibe mensajes de WhatsApp
@app.post("/whatsapp")
async def recibir_mensaje(request: Request):
    data = await request.json()
    try:
        # 📩 Extraer mensaje recibido
        entry = data.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if messages:
            mensaje = messages[0]
            numero = mensaje["from"]  # Número del usuario
            texto = mensaje["text"]["body"]  # Contenido del mensaje

            print(f"Mensaje recibido de {numero}: {texto}")

            # 🔁 Enviar respuesta
            enviar_mensaje(numero, f"Hola 👋, recibí tu mensaje: '{texto}'")

        return {"status": "ok"}
    except Exception as e:
        print("⚠️ Error procesando el mensaje:", e)
        return {"status": "error", "detail": str(e)}


# 🔹 Función para enviar mensajes a través de la API de WhatsApp
def enviar_mensaje(numero: str, texto: str):
    if not WHATSAPP_URL or not WHATSAPP_TOKEN:
        print("❌ ERROR: Falta configurar WHATSAPP_URL o WHATSAPP_TOKEN.")
        return

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {"body": texto}
    }

    response = requests.post(WHATSAPP_URL, headers=headers, json=data)

    print("➡️ Enviando mensaje...")
    print("Respuesta de la API de WhatsApp:", response.text)
