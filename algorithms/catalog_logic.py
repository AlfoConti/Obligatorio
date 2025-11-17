# algorithms/catalog_logic.py
import json, os

DATA_FILE = os.path.join("data", "products_dataset.json")

DEFAULT_PRODUCTS = [
    {"id":1,"name":"Hamburguesa Clásica","category":"Minutas","price":350},
    {"id":2,"name":"Papas Fritas","category":"Minutas","price":150},
    {"id":3,"name":"Milanesa con Papas","category":"Minutas","price":420},
    {"id":4,"name":"Pizza Margarita","category":"Pizzas","price":600},
    {"id":5,"name":"Pizza Napolitana","category":"Pizzas","price":680},
    {"id":6,"name":"Pizza Especial","category":"Pizzas","price":750},
    {"id":7,"name":"Gaseosa 500ml","category":"Bebidas","price":120},
    {"id":8,"name":"Agua Mineral 500ml","category":"Bebidas","price":80},
    {"id":9,"name":"Empanada Carne","category":"Minutas","price":120},
    {"id":10,"name":"Empanada Jamón y Queso","category":"Minutas","price":120},
    {"id":11,"name":"Ensalada César","category":"Ensaladas","price":300},
    {"id":12,"name":"Sándwich de Pollo","category":"Minutas","price":320},
    {"id":13,"name":"Lomo Completo","category":"Minutas","price":700},
    {"id":14,"name":"Postre Flan","category":"Postres","price":180},
    {"id":15,"name":"Helado 1/2 L","category":"Postres","price":250},
    {"id":16,"name":"Cerveza 330ml","category":"Bebidas","price":140},
    {"id":17,"name":"Milanesa Napolitana","category":"Minutas","price":480},
    {"id":18,"name":"Pasta Bolognesa","category":"Pastas","price":420},
    {"id":19,"name":"Ravioles","category":"Pastas","price":390},
    {"id":20,"name":"Calzone","category":"Pizzas","price":620},
    {"id":21,"name":"Tarta de Jamón y Queso","category":"Minutas","price":260},
    {"id":22,"name":"Tabla de Picadas","category":"Entradas","price":950},
    {"id":23,"name":"Pollo al Horno","category":"Minutas","price":560},
    {"id":24,"name":"Agua Saborizada","category":"Bebidas","price":95},
    {"id":25,"name":"Ensalada Mixta","category":"Ensaladas","price":240},
]

class Catalog:
    def __init__(self):
        self.products = []
        self.categories = []
        self.restaurant_coord = (-34.9011, -56.1645)
        self.load_products()

    def load_products(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                self.products = json.load(f)
        else:
            self.products = DEFAULT_PRODUCTS.copy()
        for i,p in enumerate(self.products, start=1):
            p.setdefault("id", i)
        cats = sorted(list({p.get("category","Otros") for p in self.products}))
        self.categories = ["Todos"] + cats

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

    def get_page_items_for_state(self, user_state):
        items = self.list_products(user_state.get("filter","Todos"), user_state.get("sort_asc", True))
        page = user_state.get("page", 0)
        start = page * 5
        return items[start:start+5]

    def format_menu_page_for_user_state(self, user_state):
        items = self.get_page_items_for_state(user_state)
        if not items:
            return "No hay productos en esta página."
        lines = [f"Productos (página {user_state.get('page',0)+1}):"]
        for i,p in enumerate(items, start=1):
            lines.append(f"{i}) {p['name']} - ${p['price']} ({p['category']})")
        lines.append("Opciones: Siguientes | Volver | Filtrar <categoria> | Ordenar | Seleccionar <n> | Ver carrito")
        return "\n".join(lines)

    def get_restaurant_coord(self):
        return self.restaurant_coord
