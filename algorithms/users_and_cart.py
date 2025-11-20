# algorithms/users_and_cart.py

import time
from typing import Dict, List, Optional

# ============================================================
#                    MODELO DE USUARIO
# ============================================================

class User:
    def __init__(self, phone: str):

        # Número de WhatsApp — COMPATIBILIDAD TOTAL
        self.phone = phone
        self.number = phone   # ← FIX CRÍTICO (lo pide main.py y cart_management.py)

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

        # Carrito real (solo líneas, CartManager controla totales)
        self.cart: List[dict] = []

    def reset_flow(self):
        """Reinicia el flujo del usuario."""
        self.state = "idle"
        self.pending_product_id = None
        self.pending_qty = None


# ============================================================
#                       USER MANAGER
# ============================================================

class UserManager:
    def __init__(self):
        self.users: Dict[str, User] = {}

    def get(self, phone: str) -> User:
        """Obtiene o crea un usuario por su número."""
        if phone not in self.users:
            self.users[phone] = User(phone)
        return self.users[phone]

    def set_state(self, phone: str, state: str):
        self.get(phone).state = state

    def get_state(self, phone: str) -> str:
        return self.get(phone).state

    def reset_catalog_flow(self, phone: str):
        u = self.get(phone)
        u.page = 0
        u.category = "Todos"
        u.sort = None
        u._filtered = []

    def set_pending_product(self, phone: str, prod_id: str):
        u = self.get(phone)
        u.pending_product_id = prod_id
        u.pending_qty = None


# Instancia global usada por main.py y catalog_logic.py
USERS = UserManager()
