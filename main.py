from flask import Flask, request, jsonify
from send_message import send_text, send_interactive_button, send_interactive_list
from menu_logic import process_user_message

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    try:
        message = data["entry"][0]["changes"][0]["value"]["messages"][0]
        user_number = message["from"]

        if message["type"] == "text":
            user_text = message["text"]["body"].lower()
            response = process_user_message(user_text, user_number)
            return jsonify({"status": "ok", "response": response})

        # Si el usuario toca una opción interactiva:
        if message["type"] == "interactive":
            interactive_type = list(message["interactive"].keys())[0]
            selection = message["interactive"][interactive_type]["id"]
            response = process_user_message(selection, user_number)
            return jsonify({"status": "ok", "response": response})

    except Exception as e:
        print("ERROR:", e)

    return jsonify({"status": "ignored"})


@app.route("/", methods=["GET"])
def index():
    return "Bot activo."

if __name__ == "__main__":
    app.run(port=5000, debug=True)
