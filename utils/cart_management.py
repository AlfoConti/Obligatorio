# utils/cart_management.py

# Diccionario global donde guardamos los carritos por usuario
carts = {}


def get_cart(user_id):
    """Devuelve el carrito del usuario, lo crea si no existe."""
    if user_id not in carts:
        carts[user_id] = []
    return carts[user_id]


def add_to_cart(user_id, item_name):
    """Agrega un producto al carrito del usuario."""

    cart = get_cart(user_id)

    cart.append({
        "item": item_name,
        "quantity": 1
    })

    return f"🛒 *{item_name}* fue agregado a tu carrito."


def view_cart(user_id):
    """Devuelve el contenido del carrito formateado."""

    cart = get_cart(user_id)

    if not cart:
        return "📭 *Tu carrito está vacío.*"

    msg = "🛒 *Tu carrito actual:*\n\n"
    for item in cart:
        msg += f"- {item['item']} (x{item['quantity']})\n"

    return msg


def confirm_purchase(user_id):
    """Confirma la compra y limpia el carrito."""

    cart = get_cart(user_id)

    if not cart:
        return "📭 No tenés productos en el carrito."

    total_items = len(cart)

    # Vaciar carrito
    carts[user_id] = []

    return f"🎉 *Compra confirmada*\nSe procesaron *{total_items}* productos. ¡Gracias por tu compra!"


def cancel_purchase(user_id):
    """Cancela la compra y vacía el carrito."""

    cart = get_cart(user_id)

    if not cart:
        return "📭 No tenés ninguna compra en curso."

    carts[user_id] = []

    return "❌ *Compra cancelada.* Tu carrito fue vaciado."
