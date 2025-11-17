import json
import os

DATA_PATH = os.path.join("data", "catalog.json")

class Catalog:

    @staticmethod
    def load_catalog():
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
        return [p for p in productos if p["categoria"].lower() == categoria.lower()]

    @staticmethod
    def format_category_menu():
        categorias = Catalog.get_categories()

        mensaje = "📂 *Categorías disponibles:*\n\n"
        for i, cat in enumerate(categorias, 1):
            mensaje += f"{i}) {cat}\n"

        mensaje += "\nEnviá el *número* de la categoría."
        return mensaje

    @staticmethod
    def format_products_menu(categoria):
        productos = Catalog.get_products_by_category(categoria)

        if not productos:
            return "❌ No hay productos en esta categoría."

        mensaje = f"🍽️ *Menú de {categoria}:*\n\n"

        for i, p in enumerate(productos, 1):
            mensaje += (
                f"{i}) *{p['nombre']}* - ${p['precio']}\n"
                f"   _{p['descripcion']}_\n\n"
            )

        mensaje += "Enviá el *número del producto* para agregar al pedido."
        return mensaje
