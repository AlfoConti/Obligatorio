# utils/get_type_message.py
def get_message_type(message):
    """
    Recibe el objeto 'message' del webhook de Meta y devuelve:
    - ("text", "contenido")
    - ("location", (lat, lon))
    - ("unknown", None)
    """
    if not isinstance(message, dict):
        return ("unknown", None)

    # texto
    if "text" in message and "body" in message["text"]:
        return ("text", message["text"]["body"])

    # location (estructura: message["location"] = {"latitude":..,"longitude":..})
    if "location" in message:
        loc = message["location"]
        lat = loc.get("latitude") or loc.get("lat")
        lon = loc.get("longitude") or loc.get("long") or loc.get("lng")
        if lat is not None and lon is not None:
            return ("location", (float(lat), float(lon)))

    return ("unknown", None)
