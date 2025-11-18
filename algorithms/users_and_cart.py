# algorithms/users_and_cart.py

import time
from typing import Dict, List, Optional

# ============================================
#   MODELO DE USUARIO
# ============================================

class User:
    def __init__(self, number: str):
        self.number = number
        self.created_at = time.time()

        # Datos
        self.name = None

        # Estado conversacional
        self.state = "idle"
        # idle, browsing, adding_qty, adding_note, checkout_address, waiting_location

        # Catálogo (paginación / filtros)
        self.category = "Todos"
        self.sort = None
        self.page = 0

        # Flujo de compra
        self.pending_product_id: Optional[str] = None
        self.pending_qty: Optional[int] = None

        # Carrito
        self.cart: List[dict] = []


# ============================================
#   MANEJO DE USUARIOS
# ============================================

class UserManager:
    def __init__(self):
        self.users: Dict[str, User] = {}

    def get(self, number: str) -> User:
        if number not in self.users:
            self.users[number] = User(number)
        return self.users[number]

    def reset_catalog_flow(self, number: str):
        u = self.get(number)
        u.page = 0
        u.category = "Todos"
        u.sort = None

    def set_state(self, number: str, state: str):
        self.get(number).state = state

    def get_state(self, number: str) -> str:
        return self.get(number).state

    def set_pending_product(self, number: str, prod_id: str):
        u = self.get(number)
        u.pending_product_id = prod_id
        u.pending_qty = None


# ============================================
#   CARRITO (al estilo Zustand/Redux)
# ============================================

class CartManager:
    def __init__(self):
        pass

    # helper: lectura segura de nombre / precio con fallback
    def _get_product_name(self, product: dict) -> str:
        return product.get("name") or product.get("nombre") or f"Producto-{product.get('id', '')}"

    def _get_product_price(self, product: dict) -> float:
        # intenta varias claves y convierte a float
        for k in ("price", "precio", "cost"):
            if k in product:
                try:
                    return float(product[k])
                except Exception:
                    try:
                        # si estaba en string con coma
                        return float(str(product[k]).replace(",", "."))
                    except Exception:
                        return 0.0
        return 0.0

    def add(self, user: User, product: dict, qty: int, note: str = "") -> dict:
        name = self._get_product_name(product)
        price = self._get_product_price(product)
        line = {
            "id": product.get("id"),
            "name": name,
            "price": price,
            "qty": int(qty),
            "note": note,
            "subtotal": round(price * int(qty), 2)
        }
        user.cart.append(line)
        return line

    def remove(self, user: User, product_id: str) -> bool:
        before = len(user.cart)
        user.cart = [item for item in user.cart if str(item.get("id")) != str(product_id)]
        return len(user.cart) < before

    def clear(self, user: User):
        user.cart = []

    def total(self, user: User) -> float:
        return round(sum(item.get("subtotal", 0) for item in user.cart), 2)

    def get(self, user: User):
        return user.cart

    def format(self, user: User) -> str:
        cart = user.cart
        if not cart:
            return "🛒 Tu carrito está vacío."

        msg = "🛒 *Tu carrito:*\n\n"
        for item in cart:
            msg += (
                f"*{item.get('name')}*\n"
                f"Cantidad: {item.get('qty')} – Precio: ${item.get('price')}\n"
                f"Subtotal: ${item.get('subtotal')}\n"
            )
            if item.get("note"):
                msg += f"_Nota:_ {item.get('note')}\n"
            msg += "----\n"

        msg += f"\n💰 *Total: ${self.total(user)}*"
        return msg
