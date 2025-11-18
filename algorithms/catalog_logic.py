# algorithms/catalog_logic.py

from whatsapp_service import send_whatsapp_list, send_whatsapp_text, send_whatsapp_buttons
from algorithms.users_and_cart import UserManager
from utils.cart_management import CartManager

# Instancias globales
USERS = UserManager()
CART = CartManager()

# ============================================================
# UTILIDAD: BUSCAR PRODUCTO POR ID
# ============================================================

def find_product(prod_id: str):
    """
    Simula un catálogo. Debes reemplazarlo con tu DB real.
    """
    PRODUCTS = [
        {"id": "1", "nombre": "Coca-Cola 1L", "precio": 1500},
        {"id": "2", "nombre": "Sprite 1L", "precio": 1400},
        {"id": "3", "nombre": "Fanta 1L", "precio": 1450},
    ]
    for p in PRODUCTS:
        if p["id"] == prod_id:
            return p
    return None

# ============================================================
# MENÚ PRINCIPAL DE PRODUCTOS
# ============================================================

def send_product_menu(number: str):
    user = USERS.get(number)

    # Simulación catálogo
    PRODUCTS = [
        {"id": "1", "nombre": "Coca-Cola 1L", "precio": 1500},
        {"id": "2", "nombre": "Sprite 1L", "precio": 1400},
        {"id": "3", "nombre": "Fanta 1L", "precio": 1450},
    ]

    sections = [{
        "title": "Bebidas",
        "rows": [
            {"id": f"prod_{p['id']}", "title": p["nombre"], "description": f"${p['precio']}"}
            for p in PRODUCTS
        ]
    }]

    send_whatsapp_list(
        number,
        header="Catálogo",
        body="Selecciona un producto:",
        sections=sections
    )

# ============================================================
# BOTÓN → ELEGIR CANTIDAD
# ============================================================

def request_quantity(number: str, prod_id: str):
    p = find_product(prod_id)
    if not p:
        send_whatsapp_text(number, "❌ Producto no encontrado.")
        return

    send_whatsapp_buttons(
        number,
        header=p["nombre"],
        body="¿Cuántos deseas?",
        buttons=[
            {"id": f"qty_{prod_id}_1", "title": "1"},
            {"id": f"qty_{prod_id}_2", "title": "2"},
            {"id": f"qty_{prod_id}_3", "title": "3"},
        ]
    )

# ============================================================
# PEDIR NOTA DEL PRODUCTO
# ============================================================

def ask_for_note(number: str):
    send_whatsapp_text(
        number,
        "¿Quieres agregar una nota al producto?\n\n"
        "Ej: *sin hielo*, *bien frío*\n\n"
        "Si no deseas nota, escribe: *no*"
    )

# ============================================================
# GUARDAR PRODUCTO EN EL CARRITO
# ============================================================

def save_cart_line(number: str, note: str):
    user = USERS.get(number)

    if not user.pending_product_id or not user.pending_qty:
        send_whatsapp_text(number, "❌ Error interno: faltan datos.")
        return

    product = find_product(user.pending_product_id)
    if not product:
        send_whatsapp_text(number, "❌ El producto ya no existe.")
        return

    CART.add(user, product, user.pending_qty, note)

    # reset
    user.pending_product_id = None
    user.pending_qty = None

    send_whatsapp_buttons(
        number,
        header="Producto agregado 🛒",
        body="¿Qué deseas hacer ahora?",
        buttons=[
            {"id": "cart_add_more", "title": "Agregar más"},
            {"id": "btn_carrito", "title": "Ver carrito"},
        ]
    )

# ============================================================
# VER CARRITO
# ============================================================

def send_cart(number: str):
    user = USERS.get(number)
    msg = CART.format(user)

    send_whatsapp_buttons(
        number,
        header="TU CARRITO",
        body=msg,
        buttons=[
            {"id": "cart_add_more", "title": "Agregar más"},
            {"id": "cart_edit", "title": "Editar"},
            {"id": "cart_clear", "title": "Vaciar"},
            {"id": "cart_finish", "title": "Finalizar"},
        ]
    )

# ============================================================
# MENÚ PARA ELEGIR ITEM A EDITAR
# ============================================================

def send_edit_menu(number: str):
    user = USERS.get(number)

    if not user.cart:
        send_whatsapp_text(number, "Tu carrito está vacío.")
        return

    sections = [{
        "title": "Selecciona un producto",
        "rows": [
            {
                "id": f"edit_{idx}",
                "title": item["product"]["nombre"],
                "description": f"Cantidad: {item['qty']}"
            }
            for idx, item in enumerate(user.cart)
        ]
    }]

    send_whatsapp_list(
        number,
        header="Editar carrito",
        body="Elige el producto que deseas editar:",
        sections=sections
    )

# ============================================================
# ACCIONES PARA UN ITEM DEL CARRITO
# ============================================================

def send_edit_actions(number: str, index: int):
    user = USERS.get(number)

    if index < 0 or index >= len(user.cart):
        send_whatsapp_text(number, "Ítem no válido.")
        return

    item = user.cart[index]
    product = item["product"]

    send_whatsapp_buttons(
        number,
        header=f"Editar: {product['nombre']}",
        body=f"Cantidad actual: {item['qty']}",
        buttons=[
            {"id": f"edit_qty_{index}", "title": "Cambiar cantidad"},
            {"id": f"edit_rm_{index}", "title": "Eliminar"},
        ]
    )
