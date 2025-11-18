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

    def add(self, user: User, product: dict, qty: int, note: str = "") -> dict:
        line = {
            "id": product["id"],
            "name": product["name"],
            "price": product["price"],
            "qty": qty,
            "note": note,
            "subtotal": product["price"] * qty
        }
        user.cart.append(line)
        return line

    def remove(self, user: User, product_id: str) -> bool:
        before = len(user.cart)
        user.cart = [item for item in user.cart if item["id"] != product_id]
        return len(user.cart) < before

    def clear(self, user: User):
        user.cart = []

    def total(self, user: User) -> float:
        return sum(item["subtotal"] for item in user.cart)

    def get(self, user: User):
        return user.cart

    def format(self, user: User) -> str:
        cart = user.cart
        if not cart:
            return "🛒 Tu carrito está vacío."

        msg = "🛒 *Tu carrito:*\n\n"
        for item in cart:
            msg += (
                f"*{item['name']}*\n"
                f"Cantidad: {item['qty']} – Precio: ${item['price']}\n"
                f"Subtotal: ${item['subtotal']}\n"
            )
            if item["note"]:
                msg += f"_Nota:_ {item['note']}\n"
            msg += "----\n"

        msg += f"\n💰 *Total: ${self.total(user)}*"
        return msg
