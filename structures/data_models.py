# data_models.py

import time
import random

# ====================================================================
# 1. Almacenamiento Global (Simulación de Base de Datos)
# ====================================================================

# Usamos diccionarios para simular tablas de acceso rápido por ID/Número
CLIENT_DB = {}   # {numero_whatsapp: Client_Object}
DELIVERY_DB = {} # {delivery_id: Delivery_Object}

# ====================================================================
# 2. Clases de Modelos de Datos (Estructuras)
# ====================================================================

class Product:
    """Modelo para un producto del catálogo."""
    def __init__(self, id, nombre, categoria, precio, descripcion=""):
        self.id = id
        self.nombre = nombre
        self.categoria = categoria
        self.precio = precio
        self.descripcion = descripcion
        
    def __repr__(self):
        return f"Product({self.nombre}, ${self.precio})"

class Order:
    """
    Modelo para un pedido. Es la entidad que se encola y se organiza en el ABB.
    """
    def __init__(self, order_id, client_number, products_list, total, client_location, distance, verification_code, timestamp):
        self.order_id = order_id
        self.client_number = client_number
        self.products = products_list # Lista de diccionarios del carrito
        self.total = total
        self.client_location = client_location # (lat, lon)
        self.distance = distance             # Distancia al restaurante (clave para el ABB)
        self.verification_code = verification_code
        self.timestamp = timestamp           # Tiempo de creación (para la regla de 45 min)
        self.status = "PENDING"
        self.zone = None                     # Zona de reparto (NO, NE, SO, SE)
        
    def __repr__(self):
        return f"Order(ID:{self.order_id}, Dist:{self.distance:.2f}km, Status:{self.status})"

class Client:
    """
    Modelo para un cliente. Almacena el carrito y el estado de la conversación (el grafo).
    """
    def __init__(self, number, name=None):
        self.number = number
        self.name = name or f"Cliente_{number[-4:]}" # Nombre inicial o de WhatsApp
        self.created_at = time.time()
        
        # Estructura que simula el Carrito de Compras (Punto f)
        # {product_id: {'quantity': N, 'details': 'sin tomate'}}
        self.cart = {} 
        
        # 🔑 ESTADO DEL GRAFO (Clave para flow_handler.py)
        # Define el paso actual en el proceso de venta.
        # Estados: 'start', 'selecting_product', 'soliciting_quantity', 'managing_cart', 'soliciting_location', 'break'
        self.state = 'start' 
        
        # Almacena la última página/filtro/orden visible
        self.catalog_state = {
            'page': 1, 
            'filter': 'Todos',
            'order': 'asc'
        }
        
    def __repr__(self):
        return f"Client({self.name}, State:{self.state})"
        
class Delivery:
    """
    Modelo para un repartidor. Almacena su estado y las métricas requeridas.
    """
    def __init__(self, id, name):
        self.id = id
        self.name = name
        # Estados: 'available', 'busy'
        self.state = 'available' 
        
        # 🔑 Estructura para la ruta de entrega (el Árbol Binario de Búsqueda)
        self.current_route_tree = None 
        
        # Métricas requeridas por el obligatorio (Consola)
        self.metrics = {
            'pedidos_repartidos': 0,
            'distancia_total_km': 0.0,
            'combustible_gastado_lt': 0.0
        }

    def __repr__(self):
        return f"Delivery(ID:{self.id}, State:{self.state})"
        
# ====================================================================
# 3. Funciones de Acceso a Datos (Simulación de Repositorio)
# ====================================================================

def get_or_create_client(number, name=None):
    """
    Verifica si el cliente existe o lo crea (Punto c).
    """
    if number not in CLIENT_DB:
        print(f"Creando nuevo usuario: {number}")
        CLIENT_DB[number] = Client(number, name)
    return CLIENT_DB[number]

def get_all_deliveries():
    """
    Retorna la lista de todos los deliverys (para asignación y métricas).
    """
    # Si la base de deliverys está vacía, crea unos de prueba.
    if not DELIVERY_DB:
        DELIVERY_DB[1] = Delivery(1, "Carlos (NO)")
        DELIVERY_DB[2] = Delivery(2, "Ana (NE)")
        DELIVERY_DB[3] = Delivery(3, "Pedro (SO)")
        DELIVERY_DB[4] = Delivery(4, "Maria (SE)")
        
    return list(DELIVERY_DB.values())

def update_delivery_state(delivery, new_state):
    """Actualiza el estado del delivery en la base de datos simulada."""
    delivery.state = new_state
    DELIVERY_DB[delivery.id] = delivery
    
def get_client_by_number(number):
    """Obtiene un cliente existente."""
    return CLIENT_DB.get(number)