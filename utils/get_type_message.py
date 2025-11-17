import json


def get_message_type(data):
    """
    Procesa el webhook completo de WhatsApp Cloud API y devuelve una tupla:
    (type, value)

    type puede ser:
      - "text"
      - "button"
      - "list"
      - "audio"
      - "location"
      - "image"
      - "unknown"

    value es el contenido útil (texto, id de botón, id de lista, coords, etc)
    """

    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]
        message = changes["value"]["messages"][0]
    except Exception:
        return ("unknown", None)

    msg_type = message.get("type")

    # ────────────────────────────────────────────
    # TEXTO NORMAL
    # ────────────────────────────────────────────
    if msg_type == "text":
        return ("text", message["text"]["body"])

    # ────────────────────────────────────────────
    # BOTONES
    # ────────────────────────────────────────────
    if msg_type == "interactive" and message["interactive"]["type"] == "button_reply":
        button_id = message["interactive"]["button_reply"]["id"]
        return ("button", button_id)

    # ────────────────────────────────────────────
    # LISTAS
    # ────────────────────────────────────────────
    if msg_type == "interactive" and message["interactive"]["type"] == "list_reply":
        list_id = message["interactive"]["list_reply"]["id"]
        return ("list", list_id)

    # ────────────────────────────────────────────
    # AUDIO (URL DEL AUDIO PARA TRANSCRIPCIÓN/LLM)
    # ────────────────────────────────────────────
    if msg_type == "audio":
        return ("audio", message["audio"]["id"])

    # ────────────────────────────────────────────
    # UBICACIÓN (LAT/LON)
    # ────────────────────────────────────────────
    if msg_type == "location":
        lat = message["location"]["latitude"]
        lon = message["location"]["longitude"]
        return ("location", {"lat": lat, "lon": lon})

    # ────────────────────────────────────────────
    # IMÁGENES (LINK PARA OCR, NO OBLIGATORIO)
    # ────────────────────────────────────────────
    if msg_type == "image":
        return ("image", message["image"]["id"])

    # ────────────────────────────────────────────
    # DESCONOCIDO
    # ────────────────────────────────────────────
    return ("unknown", None)
