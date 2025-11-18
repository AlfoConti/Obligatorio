import json
from utils.send_message import send_list_message, send_button_message
from utils.cart_management import get_cart

with open("data/catalog.json", "r", encoding="utf-8") as f:
    PRODUCTS = json.load(f)

PAGE_SIZE = 5

def get_categories():
    cats = set([p["category"] for p in PRODUCTS])
    return ["Todos"] + sorted(list(cats))

def filter_products(category):
    if category == "Todos":
        return PRODUCTS
    return [p for p in PRODUCTS if p["category"] == category]

def sort_products(products, ascending=True):
    return sorted(products, key=lambda x: x["price"], reverse=not ascending)

def get_page(products, page):
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    return products[start:end]

def send_product_menu(number, page=0, category="Todos", order="none"):
    products = filter_products(category)

    if order == "asc":
        products = sort_products(products, ascending=True)
    elif order == "desc":
        products = sort_products(products, ascending=False)

    page_items = get_page(products, page)

    rows = [
        {
            "id": f"product-{p['id']}",
            "title": p["name"],
            "description": f"${p['price']}"
        }
        for p in page_items
    ]

    options = []

    # FILTRAR
    options.append({
        "id": "filter-menu",
        "title": "Filtrar productos"
    })

    # ORDENAR
    options.append({
        "id": "order-price",
        "title": "Ordenar por precio"
    })

    # SIGUIENTES
    if len(products) > (page + 1) * PAGE_SIZE:
        options.append({
            "id": f"next-{page+1}",
            "title": "Siguientes productos"
        })

    # VOLVER
    if page > 0:
        options.append({
            "id": f"back-{page-1}",
            "title": "Volver (página anterior)"
        })

    # VOLVER AL INICIO
    if page >= 2:
        options.append({
            "id": "back-home",
            "title": "Volver al inicio"
        })

    sections = [
        {
            "title": f"Productos - Página {page+1}",
            "rows": rows
        },
        {
            "title": "Opciones",
            "rows": options
        }
    ]

    send_list_message(
        number,
        header="Menú de productos",
        body="Elige una opción:",
        sections=sections
    )

def send_filter_menu(number):
    cats = get_categories()

    rows = [{"id": f"cat-{c}", "title": c} for c in cats]

    sections = [
        {
            "title": "Filtrar por categoría",
            "rows": rows
        }
    ]

    send_list_message(
        number,
        header="Filtros",
        body="Selecciona una categoría:",
        sections=sections
    )
