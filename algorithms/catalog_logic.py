# algorithms/catalog_logic.py

import json
import os


CATALOG_PATH = os.path.join("data", "catalog.json")

# Estado por usuario para el catálogo
catalog_state = {}  
# Estructura del estado:
# catalog_state[user] = {
#     "page": 0,
#     "filter": "Todos",
#     "sort": "ASC" / "DESC" / None,
#     "products": [...]  # copia local filtrada/ordenada
# }


# ──────────────────────────────────────────────
# Cargar el catálogo desde JSON
# ──────────────────────────────────────────────
def load_catalog():
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


FULL_CATALOG = load_catalog()


# ──────────────────────────────────────────────
# Inicializar estado para usuario
# ──────────────────────────────────────────────
def init_user_catalog(user_phone):
    catalog_state[user_phone] = {
        "page": 0,
        "filter": "Todos",
        "sort": None,
        "products": FULL_CATALOG.copy()
    }


# ──────────────────────────────────────────────
# Aplicar filtros
# ──────────────────────────────────────────────
def apply_filter(user_phone, category):
    state = catalog_state[user_phone]
    state["filter"] = category
    state["page"] = 0  # reset

    if category == "Todos":
        state["products"] = FULL_CATALOG.copy()
    else:
        state["products"] = [
            p for p in FULL_CATALOG if p["categoria"] == category
        ]


# ──────────────────────────────────────────────
# Ordenar productos
# ──────────────────────────────────────────────
def toggle_sort(user_phone):
    state = catalog_state[user_phone]

    # alternar estado
    if state["sort"] is None or state["sort"] == "DESC":
        state["sort"] = "ASC"
    else:
        state["sort"] = "DESC"

    reverse = state["sort"] == "DESC"

    state["products"].sort(key=lambda p: p["precio"], reverse=reverse)
    state["page"] = 0  # reset


# ──────────────────────────────────────────────
# Obtener categorías disponibles
# ──────────────────────────────────────────────
def get_categories():
    categorias = sorted({p["categoria"] for p in FULL_CATALOG})
    # agregar opción Todos
    return ["Todos"] + categorias


# ──────────────────────────────────────────────
# Obtener página actual (5 productos)
# ──────────────────────────────────────────────
def get_page(user_phone):
    state = catalog_state[user_phone]
    products = state["products"]

    page = state["page"]
    start = page * 5
    end = start + 5

    return products[start:end]


# ──────────────────────────────────────────────
# Pasar a la siguiente página
# ──────────────────────────────────────────────
def next_page(user_phone):
    state = catalog_state[user_phone]
    total = len(state["products"])
    max_page = (total - 1) // 5

    if state["page"] < max_page:
        state["page"] += 1
        return True
    return False


# ──────────────────────────────────────────────
# Volver a página anterior
# ──────────────────────────────────────────────
def previous_page(user_phone):
    state = catalog_state[user_phone]
    if state["page"] > 0:
        state["page"] -= 1
        return True
    return False


# ──────────────────────────────────────────────
# Volver al inicio
# ──────────────────────────────────────────────
def go_to_start(user_phone):
    catalog_state[user_phone]["page"] = 0


# ──────────────────────────────────────────────
# Construir lista para WhatsApp (10 opciones máx.)
# ──────────────────────────────────────────────
def build_whatsapp_catalog_list(user_phone):
    """
    Devuelve un dict listo para usar en send_message()
    {
        "title": "...",
        "body": "...",
        "options": [
            {"id": "...", "title": "...", "description": "..."}
        ]
    }
    """

    state = catalog_state[user_phone]
    page_items = get_page(user_phone)

    options = []

    # Opción 1-5 → productos
    for p in page_items:
        options.append({
            "id": f"prod_{p['id']}",
            "title": f"{p['nombre']} - ${p['precio']}",
            "description": p["categoria"]
        })

    # Agregar Filtros
    options.append({"id": "filter", "title": "🔎 Filtrar por categoría", "description": ""})

    # Agregar Ordenar
    sort_txt = "↑ precio menor" if state["sort"] != "ASC" else "↓ precio mayor"
    options.append({"id": "sort", "title": f"↕ Ordenar {sort_txt}", "description": ""})

    # Siguientes productos
    if next_page_exists(user_phone):
        options.append({"id": "next", "title": "➡ Siguientes productos", "description": ""})

    # Volver si page >= 1
    if state["page"] >= 1:
        options.append({"id": "prev", "title": "⬅ Volver", "description": ""})

    # Volver al inicio si page >= 2
    if state["page"] >= 2:
        options.append({"id": "start", "title": "🏠 Volver al inicio", "description": ""})

    return {
        "title": "Catálogo",
        "body": f"Página {state['page'] + 1}",
        "options": options
    }


# ──────────────────────────────────────────────
# Siguiente página disponible?
# ──────────────────────────────────────────────
def next_page_exists(user_phone):
    st = catalog_state[user_phone]
    total = len(st["products"])
    max_page = (total - 1) // 5
    return st["page"] < max_page
