import json
import os

DATA_PATH = os.path.join("data", "catalog.json")

class Catalog:

    @staticmethod
    def load_catalog():
        if not os.path.exists(DATA_PATH):
            raise FileNotFoundError(f"❌ No se encontró el archivo del catálogo en: {DATA_PATH}")

        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def get_categories():
        productos = Catalog.load_catalog()
        categorias = sorted(set(p["categoria"] for p in productos))
        return categorias

    @staticmethod
    def get_products_by_category(categoria):
        productos = Catalog.load_catalog()
        return [
            p for p in productos
            if p["categoria"].lower() == categoria.lower()
        ]

    @staticmethod
    def get_product_by_id(product_id):
        productos = Catalog.load_catalog()
        for p in productos:
            if str(p["id"]) == str(product_id):
                return p
        return None   # importante para evitar errores

    @staticmethod
    def get_restaurant_coord():
        # Coordenadas fijas del restaurante
        return (-34.9056, -56.1867)
