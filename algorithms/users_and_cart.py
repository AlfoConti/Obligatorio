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

        # Datos
        self.name = None

        # Estado conversacional
        self.state = "idle"
        # states:
        # - idle
        # - browsing
        # - adding_qty
        # - adding_note
        # - editing
        # - checkout_address
        # - waiting_location

        # Catálogo: filtros / orden / paginado
        self.category = "Todos"
        self.sort = None
        self.page = 0
        self._filtered = []

        # Flujo de compra temporal
        self.pending_product_id: Optional[str] = None
        self.pending_qty: Optional[int] = None

        # Carrito
        # Cada item es:
        # {
        #    "product": dict,
        #    "qty": int,
        #    "note": str
        # }
        self.cart: List[dict] = []


# ============================================================
#                       USER MANAGER
# ============================================================

class UserManager:
    def __init__(self):
        self.users: Dict[str, User] = {}

    def get(self, number: str) -> User:
        """Obtiene un usuario, o lo crea si es nuevo."""
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


# ============================================================
#                         CART MANAGER
# ============================================================

class CartManager:
    def __init__(self):
        pass

    # -------------------------------
    # Helpers para obtener nombre/price
    # -------------------------------

    def _get_product_name(self, product: dict) -> str:
        return (
            product.get("nombre")
            or product.get("name")
            or f"Producto-{product.get('id','')}"
        )

    def _get_product_price(self, product: dict) -> float:
        # intenta varias claves
        for k in ("precio", "price", "cost"):
            if k in product:
                try:
                    return float(product[k])
                except:
                    try:
                        return float(str(product[k]).replace(",", "."))
                    except:
                        return 0.0
        return 0.0

    # -------------------------------
    # Add
    # -------------------------------

    def add(self, user: User, product: dict, qty: int, note: str = "") -> dict:
        """Agrega producto al carrito."""
        name = self._get_product_name(product)
        price = self._get_product_price(product)

        line = {
            "product": product,
            "qty": int(qty),
            "note": note.strip(),
            "subtotal": round(price * int(qty), 2)
        }

        user.cart.append(line)
        return line

    # -------------------------------
    # Remove por índice
    # -------------------------------

    def remove(self, user: User, index: int) -> bool:
        if 0 <= index < len(user.cart):
            user.cart.pop(index)
            return True
        return False

    # -------------------------------
    # Clear
    # -------------------------------

    def clear(self, user: User):
        user.cart = []

    # -------------------------------
    # Total
    # -------------------------------

    def total(self, user: User) -> float:
        return round(sum(item.get("subtotal", 0) for item in user.cart), 2)

    # -------------------------------
    # Get raw
    # -------------------------------

    def get(self, user: User):
        return user.cart

    # -------------------------------
    # Format carrito
    # -------------------------------

    def format(self, user: User) -> str:
        cart = user.cart

        if not cart:
            return "🛒 Tu carrito está vacío."

        msg = "🛒 *Tu carrito:*\n"

        for idx, item in enumerate(cart, start=1):
            product = item["product"]
            name = self._get_product_name(product)
            price = self._get_product_price(product)

            msg += (
                f"\n*{idx}) {name}*\n"
                f"Cantidad: {item['qty']}\n"
                f"Precio: ${price:.2f}\n"
                f"Subtotal: ${item['subtotal']:.2f}\n"
            )

            if item["note"]:
                msg += f"📝 Nota: {item['note']}\n"

        msg += f"\n💰 *Total: ${self.total(user)}*"

        return msg
