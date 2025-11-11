def get_message_type(message):
    """
    Detecta el tipo de mensaje recibido (texto, audio, ubicación, etc.)
    """
    if "text" in message:
        return "text", message["text"]["body"]
    elif "audio" in message:
        return "audio", message["audio"]["id"]
    elif "location" in message:
        location = message["location"]
        return "location", f"Lat: {location['latitude']}, Lng: {location['longitude']}"
    else:
        return "unknown", "Tipo de mensaje no reconocido"
