# algorithms/delivery_manager.py

import random
import string

from structures.data_models import DeliveryOrder
from structures.trees_and_queues import SimpleQueue
from utils.geo_calculator import process_location


# ──────────────────────────────────────────────
# CREACIÓN DE COLAS POR ZONA
# ──────────────────────────────────────────────

queues = {
    "NE": SimpleQueue(),
    "NO": SimpleQueue(),
    "SE": SimpleQueue(),
    "SO": SimpleQueue()
}


# ──────────────────────────────────────────────
# GENERAR CÓDIGO DE PEDIDO (6 caracteres)
# ──────────────────────────────────────────────
def generate_order_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


# ──────────────────────────────────────────────
# CREAR PEDIDO Y ENCOLARLO SEGÚN LA ZONA
# ──────────────────────────────────────────────
def register_delivery_order(user_id, lat, lon, cart):
    """
    Crea un pedido completo según el carrito actual y la ubicación del usuario.

    Retorna:
    {
        "ok": True,
        "order_code": "AB38F1",
        "zone": "NE",
        "time_min": 12,
        "distance_km": 4.5
    }
    """

    if not cart.items:
        return {"ok": False, "error": "El carrito está vacío."}

    # 1) Procesar ubicación
    geo = process_location(lat, lon)

    zone = geo["zone"]
    time_estimate = geo["time_min"]
    distance = geo["distance_km"]

    # 2) Generar código único
    code = generate_order_code()

    # 3) Crear objeto de pedido
    order = DeliveryOrder(
        user_id=user_id,
        order_code=code,
        zone=zone,
        latitude=lat,
        longitude=lon,
        cart_items=cart.items.copy(),
        total_amount=cart.get_total(),
        distance_km=distance,
        estimated_time=time_estimate
    )

    # 4) Encolar pedido según zona
    queues[zone].enqueue(order)

    return {
        "ok": True,
        "order_code": code,
        "zone": zone,
        "time_min": time_estimate,
        "distance_km": distance
    }


# ──────────────────────────────────────────────
# OBTENER EL PRÓXIMO PEDIDO DE UNA ZONA ESPECÍFICA
# (para reportes o para asignar delivery)
# ──────────────────────────────────────────────
def get_next_order(zone):
    if zone not in queues:
        return None
    return queues[zone].dequeue()


# ──────────────────────────────────────────────
# OBTENER TODAS LAS COLAS (para reportes globales)
# ──────────────────────────────────────────────
def get_all_queues():
    return queues
