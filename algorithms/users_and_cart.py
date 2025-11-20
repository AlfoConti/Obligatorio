# algorithms/users_and_cart.py

import time
from typing import Dict, List, Optional


# ============================================================
#                    MODELO DE USUARIO
# ============================================================

class User:
    def __init__(self, number: str):
        self.number = number
        self.created_at = time.time()

        # Datos básicos
        self.name = None

        # Estado conversacional
        self.state = "idle"

        # Catálogo
        self.category = "Todos"
        self.sort = None
        self.page = 0
        self._filtered = []

        # Flujo de compra temporal
        self.pending_product_id: Optional[str] = None
        self.pending_qty: Optional[int] = None

        # Carrito real (solo líneas, CartManager se encarga del resto)
        self.cart: List[dict] = []


# ============================================================
#                       USER MANAGER
# ============================================================

class UserManager:
    def __init__(self):
        self.users: Dict[str, User] = {}

    def get(self, number: str) -> User:
        if number not in self.users:
            self.users[number] = User(number)
        return self.users[number]

    def set_state(self, number: str, state: str):
        self.get(number).state = state

    def get_state(self, number: str) -> str:
        return self.get(number).state

    def reset_catalog_flow(self, number: str):
        u = self.get(number)
        u.page = 0
        u.category = "Todos"
        u.sort = None
        u._filtered = []

    def set_pending_product(self, number: str, prod_id: str):
        u = self.get(number)
        u.pending_product_id = prod_id
        u.pending_qty = None
