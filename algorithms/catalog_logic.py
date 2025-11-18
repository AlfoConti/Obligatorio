import json
import os

# Ruta del archivo catalog.json
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CATALOG_PATH = os.path.join(BASE_DIR, "../data/catalog.json")


def get_catalog():
    """
    Devuelve la lista completa de productos del catálogo.
    """
    try:
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("Error cargando catálogo:", e)
        return []


def get_categories():
    """
    Devuelve la lista única de categorías presentes en el catálogo.
    """
    try:
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        categorias = sorted({item["categoria"] for item in data})
        return categorias
    except Exception as e:
        print("Error cargando categorías:", e)
        return []
