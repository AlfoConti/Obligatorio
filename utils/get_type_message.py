def get_message_type(message):
    """Detecta el tipo de mensaje entrante."""
    if "text" in message:
        return "text", message["text"]["body"]

    if "button" in message:
        return "button", message["button"]["payload"]

    if "interactive" in message:
        interactive = message["interactive"]

        if "button_reply" in interactive:
            return "button", interactive["button_reply"]["id"]

        if "list_reply" in interactive:
            return "list", interactive["list_reply"]["id"]

    return "unknown", None
