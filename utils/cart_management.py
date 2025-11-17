# utils/cart_management.py

from structures.data_models import CartItem

# Carrito en memoria simple (por user)
user_carts = {}


# ---------------------------------------------------------
# Obtener carrito del usuario
# ---------------------------------------------------------
def get_cart(user_id: str):
    if user_id not in user_carts:
        user_carts[user_id] = []
    return user_carts[user_id]


# ---------------------------------------------------------
# Agregar producto
# ---------------------------------------------------------
def add_to_cart(user_id: str, product, qty: int):
    cart = get_cart(user_id)

    for item in cart:
        if item.product.id == product.id:
            item.qty += qty
            return item

    new_item = CartItem(product=product, qty=qty)
    cart.append(new_item)
    return new_item


# ---------------------------------------------------------
# Ver carrito
# ---------------------------------------------------------
def view_cart(user_id: str):
    return get_cart(user_id)


# ---------------------------------------------------------
# Quitar producto
# ---------------------------------------------------------
def remove_from_cart(user_id: str, product_id: int):
    cart = get_cart(user_id)
    new_cart = [item for item in cart if item.product.id != product_id]
    user_carts[user_id] = new_cart
    return new_cart


# ---------------------------------------------------------
# Vaciar carrito
# ---------------------------------------------------------
def clear_cart(user_id: str):
    user_carts[user_id] = []
    return []


# ---------------------------------------------------------
# Calcular total
# ---------------------------------------------------------
def get_cart_total(user_id: str):
    cart = get_cart(user_id)
    return sum(item.product.price * item.qty for item in cart)
