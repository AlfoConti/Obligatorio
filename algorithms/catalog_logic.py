# algorithms/catalog_logic.py
import json
import os
from utils.send_message import send_list_message, send_button_message

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CATALOG_PATH = os.path.join(BASE_DIR, "data", "catalog.json")

PAGE_SIZE = 5

# Load products once
with open(CATALOG_PATH, "r", encoding="utf-8") as f:
    PRODUCTS = json.load(f)

# Ensure categories list
def get_categories():
    cats = sorted(list({p.get("category","Otros") for p in PRODUCTS}))
    cats = ["Todos"] + cats
    return cats[:10]  # no más de 10

def filter_products(category):
    if not category or category == "Todos":
        return PRODUCTS
    return [p for p in PRODUCTS if p.get("category") == category]

def sort_products(products, sort_state):
    # sort_state: None, "asc", "desc"
    if sort_state == "asc":
        return sorted(products, key=lambda p: p.get("price", 0.0))
    elif sort_state == "desc":
        return sorted(products, key=lambda p: p.get("price", 0.0), reverse=True)
    return products

def make_menu_sections(products_page, session):
    # products_page: list of product dicts
    rows = []
    for p in products_page:
        rows.append({
            "id": f"prod_{p['id']}",
            "title": p.get("name"),
            "description": f"${p.get('price',0):.2f} - {p.get('category','')}"
        })

    # Controls: create control rows (max total rows 10 -> we have PAGE_SIZE product rows so up to 5 controls)
    control_rows = []

    # Filtrar
    control_rows.append({"id": "ctl_filter", "title": "🔎 Filtrar", "description": "Seleccionar categoría"})

    # Ordenar
    sort_label = "Ordenar (precio)"
    if session.get("sort") == "asc":
        sort_label += " ↑"
    elif session.get("sort") == "desc":
        sort_label += " ↓"
    control_rows.append({"id": "ctl_sort", "title": sort_label, "description": "Alterna asc/desc"})

    # Siguientes
    total_products = len(session.get("_filtered_products_cache", PRODUCTS))
    current_page = session.get("page", 0)
    if (current_page + 1) * PAGE_SIZE < total_products:
        control_rows.append({"id": f"ctl_next_{current_page+1}", "title": "➜ Siguientes", "description": "Ver próximos 5 productos"})

    # Volver
    if current_page > 0:
        control_rows.append({"id": f"ctl_prev_{current_page-1}", "title": "◀ Volver", "description": "Ver anteriores"})

    # Volver al inicio
    if current_page >= 2:
        control_rows.append({"id": "ctl_start", "title": "⤴ Volver al inicio", "description": "Ir a primera página"})

    sections = [
        {"title": f"Productos — Página {current_page+1}", "rows": rows},
        {"title": "Controles", "rows": control_rows}
    ]
    return sections

# Public API: send menu for a session
def send_product_menu(number: str, session: dict):
    """
    session is a dict stored per-user with keys:
    - page: int
    - category: str
    - sort: None/'asc'/'desc'
    We also cache filtered products inside session as '_filtered_products_cache' for quick paging.
    """

    # compute filtered & sorted list and store cache in session
    products_filtered = filter_products(session.get("category", "Todos"))
    products_sorted = sort_products(products_filtered, session.get("sort"))
    session["_filtered_products_cache"] = products_sorted

    page = session.get("page", 0)
    start = page * PAGE_SIZE
    page_items = products_sorted[start:start + PAGE_SIZE]

    sections = make_menu_sections(page_items, session)
    header = "Menú del Restaurante"
    body = f"Página {page+1} — categoría: {session.get('category','Todos')}"
    return send_list_message(number, header, body, sections)

def send_filter_menu(number: str):
    cats = get_categories()
    rows = [{"id": f"cat_{c}", "title": c, "description": ""} for c in cats]
    sections = [{"title": "Categorías", "rows": rows}]
    return send_list_message(number, "Filtrar", "Elige categoría", sections)

def request_quantity(number: str, product_id: str):
    # send buttons for quick quantities
    buttons = [
        {"id": f"qty_{product_id}_1", "title": "1"},
        {"id": f"qty_{product_id}_2", "title": "2"},
        {"id": f"qty_{product_id}_3", "title": "3"},
    ]
    return send_button_message(number, f"Ingrese cantidad para {product_id}", buttons, header="Cantidad")
