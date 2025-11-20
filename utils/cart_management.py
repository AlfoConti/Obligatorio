# utils/cart_management.py

import random
import time
from math import radians, sin, cos, sqrt, atan2

# =========================================
# DISTANCIA GEO
# =========================================

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    rlat1, rlon1, rlat2, rlon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = rlat2 - rlat1
    dlon = rlon2 - rlon1
    a = sin(dlat/2)**2 + cos(rlat1)*cos(rlat2)*sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c


# =========================================
# NUEVO CART MANAGER
# =========================================

class CartManager:

    def __init__(self):
        self.orders = []  # historial de órdenes

    # ----------------------------------------------------------
    # AGREGAR PRODUCTO
    # ----------------------------------------------------------

    def add(self, user, product: dict, qty: int, note: str = ""):
        user.cart.append({
            "product": product,
            "qty": qty,
            "note": note.strip()
        })

    # ----------------------------------------------------------
    # TOTAL
    # ----------------------------------------------------------

    def get_total(self, user):
        total = 0
        for item in user.cart:
            price = float(item["product"].get("precio", 0))
            total += price * item["qty"]
        return round(total, 2)

    # ----------------------------------------------------------
    # FORMATO
    # ----------------------------------------------------------

    def format(self, user):
        if not user.cart:
            return "🛒 *Tu carrito está vacío*"

        lines = ["🛒 *Carrito actual:*"]

        for idx, item in enumerate(user.cart, start=1):
            prod = item["product"]
            qty = item["qty"]
            price = float(prod["precio"])
            subtotal = qty * price

            note = f"\n   📝 Nota: {item['note']}" if item["note"] else ""

            lines.append(
                f"\n*{idx}) {prod['nombre']}*\n"
                f"Cantidad: {qty}\n"
                f"Precio: ${price:.2f}\n"
                f"Subtotal: ${subtotal:.2f}{note}"
            )

        lines.append(f"\n💵 *Total:* ${self.get_total(user)}")

        return "\n".join(lines)

    # ----------------------------------------------------------
    # BORRAR ITEM
    # ----------------------------------------------------------

    def remove(self, user, index: int):
        if 0 <= index < len(user.cart):
            user.cart.pop(index)
            return True
        return False

    # ----------------------------------------------------------
    # CREAR ORDEN
    # ----------------------------------------------------------

    def create_order(self, user, lat=None, lon=None):
        if not user.cart:
            return None

        order_id = len(self.orders) + 1
        code = "".join(random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ23456789", k=6))

        items = []
        total = 0

        for item in user.cart:
            prod = item["product"]
            qty = item["qty"]
            price = float(prod["precio"])

            items.append({
                "id": prod["id"],
                "nombre": prod["nombre"],
                "qty": qty,
                "price": price,
                "note": item["note"]
            })

            total += qty * price

        # -------------- FIX MÁS IMPORTANTE -------------------
        # user.phone NO EXISTE → debe ser user.number
        # -----------------------------------------------------

        order = {
            "id": order_id,
            "code": code,
            "user": user.number,     # ✔ FIX CORRECTO
            "items": items,
            "total": round(total, 2),
            "lat": lat,
            "lon": lon,
            "created_at": time.time(),
            "status": "pending"
        }

        self.orders.append(order)
        user.cart.clear()  # vaciar carrito

        return order


# =========================================
# COMPATIBILIDAD CON CÓDIGO ANTIGUO
# =========================================

CART_MANAGER = CartManager()

USERS = {}
CART = {}


def save_cart_line(user, product, qty, note):
    CART_MANAGER.add(user, product, qty, note)


def send_cart(user):
    return CART_MANAGER.format(user)


def send_edit_menu(user):
    if not user.cart:
        return "🛒 *Carrito vacío*"

    msg = "✏️ *Selecciona el ítem a editar:*\n"
    for idx, item in enumerate(user.cart, start=1):
        msg += f"\n*{idx}.* {item['product']['nombre']} (x{item['qty']})"
    return msg


def send_edit_actions():
    return (
        "✏️ *Opciones de edición:*\n"
        "1️⃣ Cambiar cantidad\n"
        "2️⃣ Cambiar nota\n"
        "3️⃣ Eliminar ítem"
    )
