# algorithms/catalog_logic.py
import json
import os

# Importaciones correctas
from whatsapp_service import (
    send_whatsapp_list,
    send_whatsapp_buttons,
)


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CATALOG_PATH = os.path.join(BASE_DIR, "data", "catalog.json")

PAGE_SIZE = 5

# Cargamos catálogo al iniciar
with open(CATALOG_PATH, "r", encoding="utf-8") as f:
    PRODUCTS = json.load(f)


# === UTILIDADES ===

def get_categories():
    cats = sorted(list({p.get("category", "Otros") for p in PRODUCTS}))
    return ["Todos"] + cats


def filter_products(category):
    if not category or category == "Todos":
        return PRODUCTS
    return [p for p in PRODUCTS if p.get("category") == category]


def sort_products(products, sort_state):
    if sort_state == "asc":
        return sorted(products, key=lambda p: p.get("price", 0.0))
    if sort_state == "desc":
        return sorted(products, key=lambda p: p.get("price", 0.0), reverse=True)
    return products


# === CREACIÓN DE OPCIONES DE MENÚ ===

def make_menu_sections(products_page, session):
    rows = []
    for p in products_page:
        rows.append({
            "id": f"prod_{p['id']}",
            "title": p["name"],
            "description": f"${p['price']:.2f} - {p.get('category','')}"
        })

    control_rows = []

    # Filtrar
    control_rows.append({
        "id": "ctl_filter",
        "title": "🔎 Filtrar",
        "description": "Seleccionar categoría"
    })

    # Ordenar
    sort_label = "Ordenar (precio)"
    if session.get("sort") == "asc":
        sort_label += " ↑"
    elif session.get("sort") == "desc":
        sort_label += " ↓"

    control_rows.append({
        "id": "ctl_sort",
        "title": sort_label,
        "description": "Alternar asc/desc"
    })

    # Paginación
    total_products = len(session.get("_filtered_products_cache", PRODUCTS))
    page = session.get("page", 0)

    if (page + 1) * PAGE_SIZE < total_products:
        control_rows.append({
            "id": f"ctl_next_{page+1}",
            "title": "➜ Siguientes",
            "description": "Ver próximos productos"
        })

    if page > 0:
        control_rows.append({
            "id": f"ctl_prev_{page-1}",
            "title": "◀ Volver",
            "description": "Página anterior"
        })

    sections = [
        {"title": f"Productos — Página {page+1}", "rows": rows},
        {"title": "Controles", "rows": control_rows}
    ]

    return sections


# === ENVÍO DE MENÚ ===

def send_product_menu(number: str, session: dict):
    """
    Muestra el menú de productos con filtros, orden y paginado.
    """

    products_filtered = filter_products(session.get("category", "Todos"))
    products_sorted = sort_products(products_filtered, session.get("sort"))
    session["_filtered_products_cache"] = products_sorted

    page = session.get("page", 0)
    start = page * PAGE_SIZE
    items = products_sorted[start:start + PAGE_SIZE]

    sections = make_menu_sections(items, session)

    header = "Menú del Restaurante"
    body = f"Página {page+1} — Categoría: {session.get('category','Todos')}"

    return send_whatsapp_list(
        number=number,
        header=header,
        body=body,
        sections=sections
    )


def send_filter_menu(number: str):
    cats = get_categories()
    rows = [{"id": f"cat_{c}", "title": c, "description": ""} for c in cats]

    sections = [{"title": "Categorías", "rows": rows}]

    return send_whatsapp_list(
        number=number,
        header="Filtrar",
        body="Selecciona una categoría",
        sections=sections
    )


def request_quantity(number: str, product_id: str):

    buttons = [
        {"id": f"qty_{product_id}_1", "title": "1"},
        {"id": f"qty_{product_id}_2", "title": "2"},
        {"id": f"qty_{product_id}_3", "title": "3"},
    ]

    return send_whatsapp_buttons(
        number=number,
        header="Cantidad",
        body=f"Ingrese cantidad para {product_id}",
        buttons=buttons
    )
