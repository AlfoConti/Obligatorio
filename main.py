# main.py
import os
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

from utils.send_message import send_whatsapp_message

app = FastAPI()
logger = logging.getLogger("uvicorn.error")

# --- In-memory store del último mensaje por usuario (teléfono) ---
# Estructura: { "59891234567": {"raw": <dict>, "text": "...", "type":"text", "received_at": 1234567890} }
last_messages = {}

# --- Health / root ---
@app.get("/")
def root():
    return {"status": "running", "service": "WhatsApp Webhook - SentinelShield"}

# --- Endpoint de verificación (Meta) ---
@app.get("/webhook")
def verify(hub_mode: str | None = None, hub_challenge: str | None = None, hub_verify_token: str | None = None):
    """
    Responde a la verificación de Meta. Si te piden algo distinto, devolvé el challenge.
    NOTA: Según tus capturas, no usás VERIFY_TOKEN. Si querés validar, compara hub_verify_token.
    """
    if hub_challenge:
        logger.info("Webhook verification request received.")
        return JSONResponse(content=hub_challenge)
    return JSONResponse(content={"msg": "Webhook endpoint. Use POST to receive messages."})

# --- Webhook receiver ---
@app.post("/webhook")
async def webhook_receiver(request: Request):
    """
    Recibe eventos desde Meta/WhatsApp (entry -> changes -> value -> messages).
    Guarda el último mensaje por número y responde con un ack.
    """
    try:
        payload = await request.json()
    except Exception as e:
        logger.exception("Invalid JSON in webhook: %s", e)
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Log completo (similar a "All logs" / Live tail)
    logger.info("Webhook payload received: %s", payload)

    # Intentar extraer mensaje según estructura de Meta
    try:
        entry = payload.get("entry", [])
        if not entry:
            logger.warning("Webhook payload without 'entry'. Ignoring.")
            return JSONResponse({"status": "ignored"})

        change = entry[0].get("changes", [])[0]
        value = change.get("value", {})
        messages = value.get("messages", [])
        if not messages:
            # Puede ser otro evento (estatus, mensajes no entregados, etc.)
            logger.info("No 'messages' in payload's value. Ignoring event.")
            return JSONResponse({"status": "no_messages"})

        msg = messages[0]  # primer mensaje
        sender = msg.get("from")  # número del usuario (wa_id)
        msg_type = msg.get("type", "unknown")

        # Extraer texto si está
        text_body = None
        if msg_type == "text":
            text_body = (msg.get("text") or {}).get("body")
        elif msg_type == "interactive":
            # interactive puede contener list_reply o button_reply
            intr = msg.get("interactive", {})
            itype = intr.get("type")
            if itype == "list_reply":
                text_body = intr.get("list_reply", {}).get("title") or intr.get("list_reply", {}).get("id")
            elif itype == "button_reply":
                text_body = intr.get("button_reply", {}).get("title") or intr.get("button_reply", {}).get("id")
            else:
                # fallback: intentar sacar body
                text_body = (msg.get("text") or {}).get("body")
        elif msg_type == "location":
            loc = msg.get("location", {})
            text_body = f"LOCATION:{loc.get('latitude')}|{loc.get('longitude')}"
        elif msg_type == "image" or msg_type == "audio" or msg_type == "video":
            text_body = f"{msg_type.upper()}_MEDIA:{msg.get(msg_type, {}).get('id')}"

        # Guardar en memoria el último mensaje para poder reenviarlo
        last_messages[sender] = {
            "raw": msg,
            "text": text_body,
            "type": msg_type
        }

        logger.info("Saved last message for %s — type=%s text=%s", sender, msg_type, text_body)

        # ACK a Meta (200) — responder algo simple
        return JSONResponse({"status": "received"})

    except Exception as e:
        logger.exception("Error processing webhook payload: %s", e)
        # devolver 200 a Meta aunque haya error para evitar retries infinitos, pero loguear
        return JSONResponse({"status": "error", "detail": str(e)})

# --- Endpoint para reenviar el último mensaje recibido al usuario ---
@app.post("/resend")
async def resend_last_message(request: Request):
    """
    Body JSON esperado:
      { "to": "59891234567" }

    Reenvía el último texto que ese número envió al bot.
    """
    try:
        body = await request.json()
        to = body.get("to")
        if not to:
            raise HTTPException(status_code=400, detail="Missing 'to' in body.")
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid JSON body.")

    last = last_messages.get(to)
    if not last:
        raise HTTPException(status_code=404, detail="No last message for that number.")

    # Enviar de vuelta el texto tal como llegó (simula "Reenviar mensaje")
    text = last.get("text") or "No textual content to resend."
    try:
        resp = send_whatsapp_message(to, f"[Reenvío] {text}")
        logger.info("Re-sent last message to %s. Response: %s", to, resp)
        return JSONResponse({"status": "resent", "to": to, "message_sent": text, "api_response": resp})
    except Exception as e:
        logger.exception("Failed to resend message: %s", e)
        raise HTTPException(status_code=500, detail="Failed to resend message.")

# --- Debug: listar últimos mensajes en memoria
@app.get("/debug/last_messages")
def debug_last_messages():
    """
    Devuelve un dict con los últimos mensajes guardados por teléfono.
    Útil para testing y ver exactamente lo que llegó en las capturas.
    """
    return last_messages
