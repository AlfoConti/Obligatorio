def get_message_type(message):
    """
    Recibe el JSON del mensaje de WhatsApp
    y devuelve una tupla: (tipo, contenido)

    Tipos:
      - "text": contenido del mensaje
      - "button": id del botón pulsado
      - "unknown": mensaje no soportado
    """

    # ======================
    #       BOTONES
    # ======================
    if "interactive" in message:
        interactive = message["interactive"]

        # Cuando el usuario presiona un botón
        if "button_reply" in interactive:
            return ("button", interactive["button_reply"]["id"])

    # ======================
    #        TEXTO
    # ======================
    if message.get("type") == "text":
        return ("text", message["text"]["body"])

    # ======================
    #      DESCONOCIDO
    # ======================
    return ("unknown", None)
