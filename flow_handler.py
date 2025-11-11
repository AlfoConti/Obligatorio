from fastapi import FastAPI, HTTPException, Request
import json
import uvicorn # Para correr el servidor
import os # Importamos os para variables de entorno

# ⚙️ IMPORTACIONES DE UTILIDADES
from utils.get_type_message import get_message_type
from utils.send_message import send_message_whatsapp

# 🧠 IMPORTACIONES DEL CORE DEL PROYECTO
from flow_handler import process_client_request # Función principal del Grafo
from structures.data_models import get_or_create_client # Manejo del Cliente (Punto c)

app = FastAPI()

# NOTA IMPORTANTE: En un proyecto real, ACCESS_TOKEN DEBE ir en variables de entorno.
# Este token se usa SOLO para la verificación inicial del Webhook (GET /whatsapp).
ACCESS_TOKEN = os.getenv("VERIFY_TOKEN", "TU_TOKEN_DE_VERIFICACION_AQUI") 

# ====================================================================
# 1. Endpoint de Verificación (GET /whatsapp)
# ====================================================================

@app.get("/whatsapp")
async def verify_token(request: Request):
    """Maneja la verificación del webhook de WhatsApp/Meta."""
    try:
        query_params = request.query_params
        verify_token = query_params.get("hub.verify_token")
        challenge = query_params.get("hub.challenge")

        # 🚨 LA LÍNEA CRÍTICA: Asegurarse de que el token coincida
        if verify_token is not None and challenge is not None and verify_token == ACCESS_TOKEN:
            # Si el token es correcto, devuelve el challenge
            return int(challenge)
        else:
            raise HTTPException(status_code=400, detail="Token de verificación inválido o parámetros faltantes")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error en la verificación: {e}")

# ====================================================================
# 2. Endpoint de Recepción de Mensajes (POST /whatsapp)
# ====================================================================

@app.post("/whatsapp")
async def received_message(request: Request):
    """Maneja los mensajes entrantes de WhatsApp."""
    try:
        body = await request.json()
        
        # Procesamiento estándar del Webhook
        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})

        # Si es una notificación de estado o lectura, la ignoramos.
        if "messages" not in value or len(value["messages"]) == 0:
            return "EVENT_RECEIVED"

        message_data = value["messages"][0]
        
        # A) ⚙️ Extracción de Datos y Tipo de Mensaje (Utilidades)
        type_message, content = get_message_type(message_data)
        number = message_data.get("from")
        
        print(f"Mensaje recibido de {number}. Tipo: {type_message}, Contenido: {content}")
        
        # B) 👤 Manejo de Cliente: Obtener o Crear (Punto c)
        client = get_or_create_client(number)
        
        # C) 🧠 Delegar la Lógica al Grafo (flow_handler.py)
        # ⚠️ Aquí es donde se genera el mensaje de respuesta (str o dict)
        response_content = process_client_request(client, type_message, content, message_data)
        
        # D) 📤 Enviar Respuesta
        if response_content:
            send_message_whatsapp(response_content, number)
            
        return "EVENT_RECEIVED"

    except Exception as e:
        print(f"Error al procesar el mensaje: {e}")
        # Se mantiene EVENT_RECEIVED para evitar reintentos de Meta
        return "EVENT_RECEIVED" 

# ====================================================================
# 3. Ejecución del Servidor
# ====================================================================

if __name__ == "__main__":
    # Comando para correr el servidor Uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)