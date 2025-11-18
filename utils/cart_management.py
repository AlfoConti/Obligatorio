# utils/cart_management.py

class CartManager:

    def add(self, user, product: dict, qty: int, note: str = ""):
        user.cart.append({
            "product": product,
            "qty": qty,
            "note": note.strip(),
            "subtotal": float(product["precio"]) * qty
        })

    def get_total(self, user):
        total = 0
        for item in user.cart:
            price = float(item["product"]["precio"])
            total += price * item["qty"]
        return round(total, 2)

    def remove(self, user, index: int):
        if 0 <= index < len(user.cart):
            user.cart.pop(index)
            return True
        return False

    def clear(self, user):
        user.cart = []

    def format(self, user):
        if not user.cart:
            return "🛒 *Tu carrito está vacío*"

        lines = ["🛒 *Carrito actual:*"]
        total = 0

        for idx, item in enumerate(user.cart, start=1):
            prod = item["product"]
            qty = item["qty"]
            price = float(prod["precio"])
            subtotal = qty * price
            total += subtotal

            note = f"\n📝 Nota: {item['note']}" if item["note"] else ""

            lines.append(
                f"\n*{idx}) {prod['nombre']}*\n"
                f"Cantidad: {qty}\n"
                f"Precio: ${price:.2f}\n"
                f"Subtotal: ${subtotal:.2f}{note}"
            )

        lines.append(f"\n💵 *Total:* ${round(total,2)}")

        return "\n".join(lines)
