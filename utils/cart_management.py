# utils/cart_management.py

"""
Carrito en memoria estilo Zustand/Redux.
Se guarda por número de teléfono.

Estructura interna:
carritos = {
   "59891234567": {
        "items": [
            {
               "id": "P23",
               "nombre": "Hamburguesa completa",
               "precio": 250,
               "cantidad": 2,
               "detalles": "Sin tomate"
            },
            {...}
        ]
   }
}
"""

carritos = {}


# ──────────────────────────────────────────────
# obtener carrito
# ──────────────────────────────────────────────
def get_cart(user_phone):
    if user_phone not in carritos:
        carritos[user_phone] = {"items": []}
    return carritos[user_phone]


# ──────────────────────────────────────────────
# agregar producto
# ──────────────────────────────────────────────
def add_to_cart(user_phone, product_id, nombre, precio, cantidad, detalles=""):
    cart = get_cart(user_phone)

    # ¿ya existe el producto en el carrito?
    for item in cart["items"]:
        if item["id"] == product_id:
            item["cantidad"] += cantidad
            if detalles:
                item["detalles"] = detalles
            return

    cart["items"].append({
        "id": product_id,
        "nombre": nombre,
        "precio": precio,
        "cantidad": cantidad,
        "detalles": detalles
    })


# ──────────────────────────────────────────────
# quitar producto
# ──────────────────────────────────────────────
def remove_from_cart(user_phone, index):
    cart = get_cart(user_phone)
    if 0 <= index < len(cart["items"]):
        cart["items"].pop(index)


# ──────────────────────────────────────────────
# vaciar carrito
# ──────────────────────────────────────────────
def clear_cart(user_phone):
    carritos[user_phone] = {"items": []}


# ──────────────────────────────────────────────
# obtener total
# ──────────────────────────────────────────────
def calculate_total(user_phone):
    cart = get_cart(user_phone)
    total = 0
    for item in cart["items"]:
        total += item["precio"] * item["cantidad"]
    return total


# ──────────────────────────────────────────────
# vista del carrito para enviar al usuario
# ──────────────────────────────────────────────
def format_cart(user_phone):
    cart = get_cart(user_phone)
    if not cart["items"]:
        return "🛒 *Tu carrito está vacío*"

    lines = ["🛒 *Carrito actual:*", ""]

    for i, item in enumerate(cart["items"]):
        subtotal = item["precio"] * item["cantidad"]
        detalle = f"\n   - _{item['detalles']}_" if item["detalles"] else ""
        lines.append(
            f"*{i+1}. {item['nombre']}*\n"
            f"   Cantidad: {item['cantidad']}\n"
            f"   Precio c/u: ${item['precio']}\n"
            f"   Subtotal: *${subtotal}*{detalle}\n"
        )

    total = calculate_total(user_phone)
    lines.append(f"*TOTAL A PAGAR: ${total}*")

    return "\n".join(lines)
