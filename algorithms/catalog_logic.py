# algorithms/catalog_logic.py

import json
import os

from whatsapp_service import (
    send_whatsapp_list,
    send_whatsapp_buttons,
    send_whatsapp_text
)

from algorithms.users_and_cart import UserManager, CartManager

# instancias globales
USERS = UserManager()
CART = CartManager()

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CATALOG_PATH = os.path.join(BASE_DIR, "data", "catalog.json")

PAGE_SIZE = 5

# ================ CARGAR CATALOGO =================

with open(CATALOG_PATH, "r", encoding="utf-8") as f:
    PRODUCTS = json.load(f)


def find_product(pid):
    for p in PRODUCTS:
        if str(p["id"]) == str(pid):
            return p
    return None


# ================ UTILIDADES =================

def get_categories():
    cats = sorted({p.get("categoria", "Otros") for p in PRODUCTS})
    return ["Todos"] + cats


def filter_products(category):
    if category == "Todos":
        return PRODUCTS
    return [p for p in PRODUCTS if p.get("categoria") == category]


def sort_products(products, sort_state):
    if sort_state == "asc":
        return sorted(products, key=lambda p: p["precio"])
    if sort_state == "desc":
        return sorted(products, key=lambda p: p["precio"], reverse=True)
    return products


# ================ SECCIONES DEL MENÚ =================

def make_menu_sections(products_page, user):
    rows = []

    for p in products_page:
        rows.append({
            "id": f"prod_{p['id']}",
            "title": p["nombre"],
            "description": f"${p['precio']} — {p.get('categoria','')}"
        })

    controls = []

    controls.append({
        "id": "ctl_filter",
        "title": "🔎 Filtrar",
        "description": "Seleccionar categoría"
    })

    sort_label = "Ordenar (precio)"
    if user.sort == "asc":
        sort_label += " ↑"
    elif user.sort == "desc":
        sort_label += " ↓"

    controls.append({
        "id": "ctl_sort",
        "title": sort_label,
        "description": "Ascendente / Descendente"
    })

    # Paginación
    page = user.page

    if (page + 1) * PAGE_SIZE < len(user._filtered):
        controls.append({
            "id": f"ctl_next_{page+1}",
            "title": "➡ Siguientes",
            "description": ""
        })

    if page > 0:
        controls.append({
            "id": f"ctl_prev_{page-1}",
            "title": "⬅ Anterior",
            "description": ""
        })

    return [
        {"title": f"Productos — Página {page+1}", "rows": rows},
        {"title": "Controles", "rows": controls}
    ]


# ================ ENVÍO DEL CATÁLOGO =================

def send_product_menu(number: str):
    user = USERS.get(number)

    filtered = filter_products(user.category)
    sorted_products = sort_products(filtered, user.sort)

    user._filtered = sorted_products

    start = user.page * PAGE_SIZE
    page_items = sorted_products[start:start + PAGE_SIZE]

    sections = make_menu_sections(page_items, user)

    return send_whatsapp_list(
        number,
        header="Menú del Restaurante",
        body=f"Página {user.page+1} — Categoría {user.category}",
        sections=sections
    )


# ================ MENÚ DE FILTRO =================

def send_filter_menu(number: str):
    cats = get_categories()

    rows = [{
        "id": f"cat_{c}",
        "title": c,
        "description": ""
    } for c in cats]

    sections = [{"title": "Categorías", "rows": rows}]

    return send_whatsapp_list(
        number,
        header="Filtrar productos",
        body="Selecciona una categoría",
        sections=sections
    )


# ================ PEDIR CANTIDAD =================

def request_quantity(number: str, prod_id: str):
    user = USERS.get(number)

    product = find_product(prod_id)
    if not product:
        return send_whatsapp_text(number, "❌ Producto no encontrado.")

    USERS.set_pending_product(number, prod_id)
    USERS.set_state(number, "adding_qty")

    buttons = [
        {"id": f"qty_{prod_id}_1", "title": "1"},
        {"id": f"qty_{prod_id}_2", "title": "2"},
        {"id": f"qty_{prod_id}_3", "title": "3"},
    ]

    return send_whatsapp_buttons(
        number,
        header=product["nombre"],
        body="Selecciona una cantidad:",
        buttons=buttons
    )


# ================ PEDIR NOTA =================

def ask_for_note(number: str):
    user = USERS.get(number)
    USERS.set_state(number, "adding_note")

    return send_whatsapp_text(
        number,
        "¿Quieres agregar una nota? (ej: “sin tomate”)\n"
        "Si no deseas nota, escribe: *no*"
    )


# ================ GUARDAR LÍNEA DE CARRITO =================

def save_cart_line(number: str, note: str = ""):
    user = USERS.get(number)

    prod = find_product(user.pending_product_id)
    if not prod:
        return send_whatsapp_text(number, "❌ Error: producto no encontrado.")

    CART.add(user, prod, user.pending_qty, note)

    # reset
    user.pending_product_id = None
    user.pending_qty = None
    USERS.set_state(number, "browsing")

    return send_cart(number)


# ============================================================
#                     MOSTRAR CARRITO
# ============================================================

def send_cart(number: str):
    """
    Muestra el carrito con botones correctos (3 botones máximo permitido por WhatsApp).
    """
    user = USERS.get(number)

    text = CART.format(user)

    buttons = [
        {"id": "cart_finish", "title": "✅ Finalizar pedido"},
        {"id": "cart_add_more", "title": "➕ Agregar otro producto"},
        {"id": "cart_edit", "title": "🛠 Editar carrito"},
    ]

    return send_whatsapp_buttons(
        number,
        header="Tu Carrito",
        body=text,
        buttons=buttons
    )


# ============================================================
#                 MENÚ PARA EDITAR CARRITO
# ============================================================

def send_edit_menu(number: str):
    user = USERS.get(number)

    if not user.cart:
        return send_whatsapp_text(number, "🛒 Tu carrito está vacío.")

    rows = []

    for idx, item in enumerate(user.cart):
        prod = item["product"]
        rows.append({
            "id": f"edit_{idx}",
            "title": prod["nombre"],
            "description": f"Cantidad: {item['qty']}"
        })

    return send_whatsapp_list(
        number,
        header="Editar carrito",
        body="Selecciona un producto:",
        sections=[{
            "title": "Productos en tu carrito",
            "rows": rows
        }]
    )


# ============================================================
#           ACCIONES SOBRE UN PRODUCTO (EDITAR/BORRAR)
# ============================================================

def send_edit_actions(number: str, index: int):
    user = USERS.get(number)
    item = user.cart[index]
    prod = item["product"]

    buttons = [
        {"id": f"edit_qty_{index}", "title": "Cambiar cantidad"},
        {"id": f"edit_rm_{index}", "title": "❌ Quitar"},
    ]

    return send_whatsapp_buttons(
        number,
        header=prod["nombre"],
        body="¿Qué acción deseas realizar?",
        buttons=buttons
    )
