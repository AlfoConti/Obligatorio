CART = {}

def add_to_cart(user, product, qty, note):
    if user not in CART:
        CART[user] = []

    CART[user].append({
        "product": product,
        "qty": qty,
        "note": note,
        "subtotal": product["price"] * qty
    })

def get_cart(user):
    return CART.get(user, [])

def remove_item(user, product_id):
    if user not in CART:
        return
    CART[user] = [p for p in CART[user] if p["product"]["id"] != product_id]
