# utils/get_type_message.py
def get_message_type(message: dict):
    if not isinstance(message, dict):
        return "unknown", None
    if "text" in message and isinstance(message["text"], dict):
        return "text", message["text"].get("body", "")
    if "location" in message:
        loc = message["location"]
        return "location", (loc.get("latitude"), loc.get("longitude"))
    return "unknown", None
