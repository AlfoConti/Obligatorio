# dentro de algorithms/users_and_cart.py reemplaza la clase CartManager por esta

import random
import time
from math import ceil
from typing import Optional

from utils.geo_calculator import haversine_km  # usa tu módulo existente


class CartManager:
    """
    CartManager unificado:
    - estructura de items: {"product": dict, "qty": int, "note": str, "subtotal": float}
    - métodos: add, increment, decrement, remove, clear, total, get, format, update_subtotals, create_order
    """

    def __init__(self, restaurant_coord: tuple = (-34.9011, -56.1645)):
        self.orders = []  # historial de órdenes (ordenes confirmadas)
        self.restaurant_coord = restaurant_coord

    # -------------------------
    # Helpers internos
    # -------------------------
    def _get_product_name(self, product: dict) -> str:
        return product.get("nombre") or product.get("name") or f"Producto-{product.get('id','')}"

    def _get_product_price(self, product: dict) -> float:
        for k in ("precio", "price", "cost"):
            if k in product:
                try:
                    return float(product[k])
                except Exception:
                    try:
                        return float(str(product[k]).replace(",", "."))
                    except Exception:
                        return 0.0
        return 0.0

    def _gen_code6(self) -> str:
        return "".join(random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ23456789", k=6))

    # -------------------------
    # Add
    # -------------------------
    def add(self, user, product: dict, qty: int, note: str = "") -> dict:
        """
        Añade una línea al carrito del user. Valida qty y calcula subtotal.
        """
        try:
            qty = int(qty)
            if qty <= 0:
                qty = 1
        except Exception:
            qty = 1

        price = self._get_product_price(product)
        line = {
            "product": product,
            "qty": qty,
            "note": (note or "").strip(),
            "subtotal": round(price * qty, 2)
        }
        if not hasattr(user, "cart") or user.cart is None:
            user.cart = []
        user.cart.append(line)
        return line

    # -------------------------
    # Update subtotals
    # -------------------------
    def update_subtotals(self, user) -> None:
        """Recalcula subtotales y total después de editar cantidades."""
        if not getattr(user, "cart", None):
            return
        for item in user.cart:
            price = self._get_product_price(item["product"])
            item["subtotal"] = round(price * int(item.get("qty", 0)), 2)

    # -------------------------
    # Increment / Decrement
    # -------------------------
    def increment(self, user, index: int) -> bool:
        if not getattr(user, "cart", None):
            return False
        if 0 <= index < len(user.cart):
            user.cart[index]["qty"] = int(user.cart[index]["qty"]) + 1
            self.update_subtotals(user)
            return True
        return False

    def decrement(self, user, index: int) -> bool:
        if not getattr(user, "cart", None):
            return False
        if 0 <= index < len(user.cart):
            if int(user.cart[index]["qty"]) > 1:
                user.cart[index]["qty"] = int(user.cart[index]["qty"]) - 1
                self.update_subtotals(user)
                return True
        return False

    # -------------------------
    # Remove / Clear
    # -------------------------
    def remove(self, user, index: int) -> bool:
        if not getattr(user, "cart", None):
            return False
        if 0 <= index < len(user.cart):
            user.cart.pop(index)
            return True
        return False

    def clear(self, user) -> None:
        user.cart = []

    # -------------------------
    # Totals / Get
    # -------------------------
    def total(self, user) -> float:
        if not getattr(user, "cart", None):
            return 0.0
        return round(sum(item.get("subtotal", 0.0) for item in user.cart), 2)

    def get(self, user):
        return user.cart if getattr(user, "cart", None) else []

    # -------------------------
    # Format (texto para WhatsApp)
    # -------------------------
    def format(self, user) -> str:
        cart = self.get(user)
        if not cart:
            return "🛒 Tu carrito está vacío."

        msg_lines = ["🛒 *Tu carrito:*\n"]
        for idx, item in enumerate(cart, start=1):
            prod = item["product"]
            name = self._get_product_name(prod)
            price = self._get_product_price(prod)
            note = item.get("note", "")
            msg_lines.append(
                f"*{idx}) {name}*\n"
                f"Cantidad: {item['qty']}\n"
                f"Precio uni: ${price:.2f}\n"
                f"Subtotal: ${item['subtotal']:.2f}\n"
            )
            if note:
                msg_lines.append(f"📝 Nota: {note}\n")
        msg_lines.append(f"\n💰 *Total: ${self.total(user)}*")
        return "\n".join(msg_lines)

    # -------------------------
    # Crear orden (temporal en el prototipo)
    # -------------------------
    def create_order(self, user, lat: Optional[float] = None, lon: Optional[float] = None):
        """
        Crea una orden a partir del carrito, calcula distancia y ETA si lat/lon se proveen,
        genera código de 6 chars y agrega a historial self.orders.
        Devuelve la orden dict.
        """
        cart = self.get(user)
        if not cart:
            return None

        # construir items
        items = []
        total = 0.0
        for it in cart:
            prod = it["product"]
            qty = int(it["qty"])
            price = self._get_product_price(prod)
            subtotal = round(price * qty, 2)
            items.append({
                "id": prod.get("id"),
                "nombre": prod.get("nombre"),
                "qty": qty,
                "price": price,
                "note": it.get("note", ""),
                "subtotal": subtotal
            })
            total += subtotal

        order_id = len(self.orders) + 1
        code6 = self._gen_code6()
        now_ts = time.time()

        order = {
            "id": order_id,
            "code": code6,
            "user": user.number if hasattr(user, "number") else getattr(user, "phone", None),
            "items": items,
            "total": round(total, 2),
            "lat": lat,
            "lon": lon,
            "created_at": now_ts,
            "status": "pending"
        }

        # calcular distancia y ETA si hay coords
        if lat is not None and lon is not None:
            try:
                dist_km = haversine_km(self.restaurant_coord[0], self.restaurant_coord[1], float(lat), float(lon))
                # estimación simple: 0.5 km/min -> 10 km = 20 min
                eta_min = max(5, int(ceil(dist_km / 0.5)))
                order["distance_km"] = round(dist_km, 2)
                order["eta_min"] = eta_min
            except Exception:
                order["distance_km"] = None
                order["eta_min"] = None
        else:
            order["distance_km"] = None
            order["eta_min"] = None

        self.orders.append(order)

        # vaciar carrito del usuario
        self.clear(user)

        return order
