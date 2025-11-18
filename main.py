from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from algorithms.catalog_logic import get_catalog, get_categories

app = FastAPI()

# CORS (necesario para permitir llamadas desde tu frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "API funcionando correctamente"}

# === ENDPOINT CATÁLOGO ===
@app.get("/catalog")
def catalog():
    """
    Devuelve todos los productos del catálogo.
    """
    return get_catalog()

# === ENDPOINT CATEGORÍAS ===
@app.get("/categories")
def categories():
    """
    Devuelve las categorías únicas.
    """
    return get_categories()
