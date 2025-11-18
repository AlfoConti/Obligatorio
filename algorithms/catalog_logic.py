# algorithms/catalog_logic.py
import json
import os
from math import isclose

# Intentamos varias rutas para encontrar el JSON del catálogo
CANDIDATE_PATHS = [
    os.path.join("data", "catalog.json"),
    os.path.join("algorithms", "catalog.json"),
    os.path.join("data", "products_dataset.json")
]

def _find_catalog_path():
    for p in CANDIDATE_PATHS:
        if os.path.exists(p):
            return p
    return None

class Catalog:
    def __init__(self):
        self._path = _find_catalog_path()
        if not self._path:
            raise FileNotFoundError("No se encontró data/catalog.json ni algorithms/catalog.json. Subí el archivo.")
        self.products = self.load_catalog()
        # normalizamos claves para que el resto del código use 'name','category','price','description','id'
        self._normalize_products()

    def load_catalog(self):
        with open(self._path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _normalize_products(self):
        norm = []
        for p in self.products:
            np = {}
            np['id'] = p.get('id') or p.get('ID') or p.get('Id')
            # nombre -> name
            np['name'] = p.get('nombre') or p.get('name') or p.get('title') or p.get('titulo') or "Producto"
            # categoria -> category
            np['category'] = p.get('categoria') or p.get('category') or "Otros"
            # precio -> price
            np['price'] = p.get('precio') or p.get('price') or 0
            # descripcion -> description
            np['description'] = p.get('descripcion') or p.get('description') or p.get('desc') or ""
            norm.append(np)
        self.products = norm

    def get_categories(self):
        cats = sorted({p['category'] for p in self.products})
        return cats

    def get_products_by_category(self, category):
        return [p for p in self.products if p['category'].lower() == category.lower()]

    def get_product_by_id(self, product_id):
        for p in self.products:
            try:
                if str(p['id']) == str(product_id):
                    return p
            except Exception:
                continue
        return None

    def get_restaurant_coord(self):
        # Coordenadas por defecto del restaurante (puedes cambiarlas)
        return (-34.9011, -56.1645)

    # helpers para paginado y estado de usuario
    def get_page_items_for_state(self, user_state):
        """
        Retorna la lista de items (normalizados) que debe mostrarse
        según filtro y orden del user_state.
        """
        items = list(self.products)
        fil = user_state.get("filter")
        if fil:
            items = [p for p in items if p['category'].lower() == fil.lower()]

        sort_asc = user_state.get("sort_asc", True)
        items = sorted(items, key=lambda x: float(x.get('price', 0)), reverse=not sort_asc)
        return items

    def format_menu_page_for_user_state(self, user_state):
        """
        Construye el texto del menú con paginado de 5 items.
        user_state keys:
          - page (int)
          - filter (str)
          - sort_asc (bool)
        """
        page = int(user_state.get("page", 0))
        page_size = 5
        all_items = self.get_page_items_for_state(user_state)
        total = len(all_items)
        start = page * page_size
        end = start + page_size
        page_items = all_items[start:end]

        if not page_items:
            return "No hay productos para mostrar."

        lines = []
        lines.append(f"📄 *Página {page+1}*  (mostrando {start+1}-{min(end,total)} de {total})\n")
        if user_state.get("filter"):
            lines.append(f"Filtrado por: *{user_state.get('filter')}*\n")
        for idx, p in enumerate(page_items, start=1):
            lines.append(f"{idx}) *{p['name']}* - ${p['price']}\n   _{p['description']}_\n")

        # opciones de navegación
        nav = []
        if end < total:
            nav.append("Siguientes")
        if page > 0:
            nav.append("Volver")
        nav.append("Filtrar <categoria>")
        nav.append("Ordenar")
        nav.append("Seleccionar <n>")
        lines.append("Comandos: " + " | ".join(nav))
        return "\n".join(lines)
