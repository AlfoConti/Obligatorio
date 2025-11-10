from fastapi import FastAPI, HTTPException, Request
import json
import uvicorn # Para correr el servidor

# ⚙️ IMPORTACIONES DE UTILIDADES
from utils.get_type_message import get_message_type
from utils.send_message import send_message_whatsapp

# 🧠 IMPORTACIONES DEL CORE DEL PROYECTO
from flow_handler import process_client_request # Función principal del Grafo
from structures.data_models import get_or_create_client # Manejo del Cliente (Punto c)

app = FastAPI()

# NOTA: En un proyecto real, ACCESS_TOKEN DEBE ir en variables de entorno (.env)
# Usa tu token de verificación configurado en Meta
ACCESS_TOKEN = "TU_TOKEN_DE_VERIFICACION_AQUI" 

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

        if verify_token is not None and challenge is not None and verify_token == ACCESS_TOKEN:
            # Si el token es correcto, devuelve el challenge
            return int(challenge)
        else: # Corregido 'otra cosaA'
            raise HTTPException(status_code=400, detail="Token de verificación inválido o parámetros faltantes")
    except Exception as e: # Corregido 'excepto Excepción'
        raise HTTPException(status_code=400, detail=f"Error en la verificación: {e}")

# ====================================================================
# 2. Endpoint de Recepción de Mensajes (POST /whatsapp)
# ====================================================================

@app.post("/whatsapp")
async def received_message(request: Request): # Corregida la firma de la función
    """Maneja los mensajes entrantes de WhatsApp."""
    try:
        body = await request.json()
        
        # Procesamiento estándar del Webhook (Corregido el nombramiento de variables a inglés estándar)
        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})

        if "messages" in value and len(value["messages"]) > 0:
            message_data = value["messages"][0]
            
            # A) ⚙️ Extracción de Datos y Tipo de Mensaje (Utilidades)
            type_message, content = get_message_type(message_data) # Corregida variable 'contenido' a 'content'
            number = message_data.get("from") # Corregida variable 'număr' y clave a "from"
            
            print(f"Mensaje recibido de {number}. Tipo: {type_message}, Contenido: {content}") # Corregido 'imprimir'
            
            # B) 👤 Manejo de Cliente: Obtener o Crear (Punto c)
            client = get_or_create_client(number) # Corregida variable 'cliente' a 'client'
            
            # C) 🧠 Delegar la Lógica al Grafo (flow_handler.py)
            response_message_text = process_client_request(client, type_message, content, message_data) # Corregidos nombres de función y variables
            
            # D) 📤 Enviar Respuesta
            if response_message_text: # Corregido 'si'
                send_message_whatsapp(response_message_text, number)
                
        return "EVENT_RECEIVED" # Corregido 'devuelve "EVENTO_RECIBIDO"'

    except Exception as e:
        print(f"Error al procesar el mensaje: {e}")
        # Se mantiene EVENT_RECEIVED para evitar reintentos de Meta
        return "EVENT_RECEIVED" 

# ====================================================================
# 3. Ejecución del Servidor
# ====================================================================

if __name__ == "__main__": # Corregido 'if __name__ == "__main__"A'
    # Comando para correr el servidor Uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) # Corregida variable 'aplicación'