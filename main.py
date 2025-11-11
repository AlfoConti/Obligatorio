from flask import Flask, request, jsonify
from utils.send_message import send_whatsapp_message
from utils.get_type_message import get_message_type

import os

app = Flask(__name__)

# 👉 Token para verificar el webhook con Meta
VERIFY_TOKEN = "mi_token_verificacion"  # este lo elegís vos (lo ponés también en Meta)

@app.route('/webhook', methods=['GET'])
def verify_token():
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    if token == VERIFY_TOKEN:
        return challenge
    return "Token inválido", 403


@app.route('/webhook', methods=['POST'])
def receive_message():
    data = request.get_json()
    print("📩 Nuevo mensaje recibido:", data)

    # Verificamos si el mensaje viene en el formato esperado
    if "entry" in data:
        for entry in data["entry"]:
            for change in entry["changes"]:
                value = change["value"]
                if "messages" in value:
                    message = value["messages"][0]
                    phone_number = value["metadata"]["display_phone_number"]
                    sender = message["from"]
                    message_type, message_content = get_message_type(message)

                    print(f"Mensaje de {sender}: {message_content} (tipo: {message_type})")

                    # Ejemplo simple: responder con un texto
                    send_whatsapp_message(sender, f"Recibí tu mensaje: {message_content}")

    return jsonify({"status": "ok"}), 200


if __name__ == '__main__':
    app.run(debug=True)
