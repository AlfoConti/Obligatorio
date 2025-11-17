from send_message import send_interactive_button, send_interactive_list, send_text

def process_user_message(text, user):

    # PRIMERA ENTRADA (cuando escriben menu)
    if text in ["menu", "menú", "hola", "start"]:
        return send_interactive_button(
            user,
            "Elige una categoría:",
            "Ver menú",
            "categoria_menu"
        )

    # CUANDO TOCAN EL BOTÓN
    if text == "categoria_menu":
        sections = [
            {
                "title": "Hamburguesas",
                "rows": [
                    {"id": "whopper", "title": "Whopper"},
                    {"id": "doble_whopper", "title": "Doble Whopper"},
                ]
            },
            {
                "title": "Acompañamientos",
                "rows": [
                    {"id": "papas", "title": "Papas fritas"},
                    {"id": "aros", "title": "Aros de cebolla"},
                ]
            },
            {
                "title": "Bebidas",
                "rows": [
                    {"id": "coca", "title": "Coca-Cola"},
                    {"id": "sprite", "title": "Sprite"},
                ]
            }
        ]

        return send_interactive_list(
            user,
            "Menú BK",
            "Selecciona el producto que quieras ver:",
            sections
        )

    # RESPUESTAS DE PRODUCTOS
    productos = {
        "whopper": "🍔 *Whopper*\nCarne a la parrilla, tomate, lechuga y más.",
        "doble_whopper": "🍔 *Doble Whopper*\nDos carnes flameadas a la parrilla.",
        "papas": "🍟 *Papas fritas*\nClásicas y crocantes.",
        "aros": "🧅 *Aros de cebolla*\nCrujientes y dorados.",
        "coca": "🥤 *Coca-Cola*",
        "sprite": "🥤 *Sprite*",
    }

    if text in productos:
        return send_text(user, productos[text])

    # fallback
    return send_text(user, "Escribe *menu* para ver las opciones.")
