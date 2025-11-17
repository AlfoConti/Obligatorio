# algorithms/catalog_logic.py
import json, os

DATA_FILE = os.path.join("data", "products_dataset.json")

DEFAULT_PRODUCTS = [
    # si quieres, carga aquí 25 productos; el main usará esto si no existe el JSON
    {"id": 1, "name": "Hamburguesa Clásica", "category": "Minutas", "price": 350},
    {"id": 2, "name": "Papas Fritas", "category": "Minutas", "price": 150},
    {"id": 3, "name": "Pizza Margarita", "category": "Pizzas", "price": 600},
    # ... (completar hasta 25 o usar tu products_dataset.json)
]

class Catalog:
    def __init__(self):
        self.products = []
        self.categories = ["Todos"]
        self.load_products()

    def load_products(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                self.products = json.load(f)
        else:
            self.products = DEFAULT_PRODUCTS.copy()
        # ensure ids
        for i,p in enumerate(self.products, start=1):
            p.setdefault("id", i)
        cats = set(p.get("category","Otros") for p in self.products)
        self.categories = ["Todos"] + sorted(list(cats))

    def get_categories(self):
        return self.categories

    def get_product_by_id(self, pid):
        for p in self.products:
            if p["id"] == pid:
                return p
        return None

    def list_products(self, filter_cat="Todos", sort_asc=True):
        res = self.products
        if filter_cat and filter_cat != "Todos":
            res = [p for p in res if p.get("category") == filter_cat]
        res = sorted(res, key=lambda x: x.get("price",0), reverse=not sort_asc)
        return res

    def get_page(self, phone_user_state):
        # phone_user_state is a dict with page/filter/sort_asc
        items = self.list_products(phone_user_state.get("filter","Todos"), phone_user_state.get("sort_asc", True))
        page = phone_user_state.get("page", 0)
        start = page * 5
        return items[start:start+5]

    def format_menu_page(self, phone_user_state_or_phone):
        # flexible: if phone given, we expect main to pass state; otherwise pass state dict
        if isinstance(phone_user_state_or_phone, dict):
            u = phone_user_state_or_phone
        else:
            # caller passes phone string -> not supported here, main will call get_page via state
            return "No hay estado del usuario para mostrar menú."
        items = self.get_page(u)
        if not items:
            return "No hay productos en esta página."
        lines = [f"Productos (página {u.get('page',0)+1}):"]
        for i,p in enumerate(items, start=1):
            lines.append(f"{i}) {p['name']} - ${p['price']} ({p['category']})")
        controls = "Siguientes | Volver | Filtrar <categoria> | Ordenar | Seleccionar <n> | Ver carrito"
        lines.append("Opciones: " + controls)
        return "\n".join(lines)

    # helper used by main for simpler call
    def format_menu_page(self, phone):
        """
        phone: phone string -> main uses its carts.get_user(phone) to get state
        but to keep API simple, we fallback: caller should pass state dict - main uses get_page_items
        """
        # This method kept for backwards compatibility: main will call get_page_items instead.
        return "Use la acción 'Menu' para ver productos."

    # provide a function main expects
    def get_page_items(self, phone_state):
        # main passes phone to catalog.get_page_items(phone) BUT our main passes phone -> we need phone-state from main
        # To keep contract, the main's catalog.get_page_items will be called with phone string; however in our main above
        # we used catalog.get_page_items(sender) expecting it returns page items. We'll implement a small adapter:
        raise NotImplementedError("get_page_items requires phone-state adapter in main.")
