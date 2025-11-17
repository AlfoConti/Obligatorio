# Carrito temporal almacenado en memoria
# Estructura:
# carts = {
#     "5989123456": [
#         {
#             "id": "p001",
#             "name": "Hamburguesa",
#             "price": 250,
#             "qty": 2,
#             "subtotal": 500
#         }
#     ]
# }
carts = {}

# -------------------------------------------
# CREAR CARRITO SI NO EXISTE
# -------------------------------------------
def ensure_cart(phone):
    if phone not in carts:
        carts[phone] = []


# -------------------------------------------
# AGREGAR PRODUCTO AL CARRITO
# -------------------------------------------
def add_to_cart(phone, product, quantity):
    ensure_cart(phone)

    # ¿Existe ya en carrito?
    for item in carts[phone]:
        if item["id"] == product["id"]:
            item["qty"] += quantity
            item["subtotal"] = item["qty"] * item["price"]
            return

    # Si es nuevo
    carts[phone].append({
        "id": product["id"],
        "name": product["name"],
        "price": product["price"],
        "qty": quantity,
        "subtotal": product["price"] * quantity
    })


# -------------------------------------------
# QUITAR PRODUCTO POR ID
# -------------------------------------------
def remove_from_cart(phone, product_id):
    ensure_cart(phone)
    carts[phone] = [item for item in carts[phone] if item["id"] != product_id]


# -------------------------------------------
# VACIAR CARRITO
# -------------------------------------------
def clear_cart(phone):
    carts[phone] = []


# -------------------------------------------
# OBTENER CARRITO FORMATEADO
# -------------------------------------------
def get_cart_summary(phone):
    ensure_cart(phone)

    if len(carts[phone]) == 0:
        return "🛒 Tu carrito está vacío."

    text = "🛒 *TU CARRITO*\n\n"
    total = 0

    for item in carts[phone]:
        text += f"• *{item['name']}* x{item['qty']} — ${item['subtotal']}\n"
        total += item["subtotal"]

    text += f"\n💰 *Total:* ${total}"

    return text


# -------------------------------------------
# OBTENER CARRITO (SIN FORMATO)
# -------------------------------------------
def get_cart_items(phone):
    ensure_cart(phone)
    return carts[phone]


# -------------------------------------------
# OBTENER TOTAL DEL CARRITO
# -------------------------------------------
def get_cart_total(phone):
    ensure_cart(phone)
    return sum(item["subtotal"] for item in carts[phone])
