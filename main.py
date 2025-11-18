from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from algorithms.catalog_logic import get_catalog, get_categories

app = FastAPI()

# === CORS ===
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

@app.get("/catalog")
def catalog():
    return get_catalog()

@app.get("/categories")
def categories():
    return get_categories()


# === ESTE BLOQUE ES OBLIGATORIO PARA RENDER ===
# SIN ESTO LA APP SE CIERRA Y DA "Application exited early"
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=10000,
        reload=False
    )
