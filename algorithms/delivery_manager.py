# algorithms/delivery_manager.py
import time
import random
import string
from collections import deque
from math import radians, sin, cos, sqrt, atan2
from typing import Dict, List, Optional, Any

# ------------------------
# UTIL: haversine
# ------------------------
def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    rlat1, rlon1, rlat2, rlon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = rlat2 - rlat1
    dlon = rlon2 - rlon1
    a = sin(dlat/2)**2 + cos(rlat1)*cos(rlat2)*sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

# ------------------------
# CONSTANTS & CONFIG
# ------------------------
RESTAURANT_COORDS = (-34.905, -56.191)  # ejemplo: Montevideo (ajustar si hace falta)
TANDA_MAX = 7
TANDA_MAX_WAIT_SECONDS = 45 * 60  # 45 minutos
KM_TO_MIN = 2.0  # convertir km a minutos estimados (por km)
BASE_PREP_MIN = 10  # tiempo base de preparación (minutos)
LITERS_PER_KM = 0.1  # 1 litro cada 10 km -> 0.1 L/km

# ------------------------
# Helpers
# ------------------------
def generate_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + "23456789", k=length))

def zone_from_coords(lat, lon, center=RESTAURANT_COORDS):
    lat_c, lon_c = center
    if lat >= lat_c and lon >= lon_c:
        return "NE"
    if lat >= lat_c and lon < lon_c:
        return "NO"
    if lat < lat_c and lon >= lon_c:
        return "SE"
    return "SO"

# ------------------------
# BST helper (balanced) for delivery ordering by distance
# We'll build a simple balanced tree structure from a sorted list
# and expose an inorder traversal (closest -> farthest).
# ------------------------
class BSTNode:
    def __init__(self, order: dict):
        self.order = order
        self.left: Optional['BSTNode'] = None
        self.right: Optional['BSTNode'] = None

def build_balanced_bst(sorted_orders: List[dict]) -> Optional[BSTNode]:
    if not sorted_orders:
        return None
    mid = len(sorted_orders) // 2
    root = BSTNode(sorted_orders[mid])
    root.left = build_balanced_bst(sorted_orders[:mid])
    root.right = build_balanced_bst(sorted_orders[mid+1:])
    return root

def inorder_traversal(node: Optional[BSTNode], out: List[dict]):
    if not node:
        return
    inorder_traversal(node.left, out)
    out.append(node.order)
    inorder_traversal(node.right, out)

# ------------------------
# DeliveryManager
# ------------------------
class DeliveryManager:
    def __init__(self):
        # registro de repartidores y su estado
        # delivery_id -> dict(status: "available"|"busy", assigned_tanda_id: Optional[int], stats: {...})
        self.deliveries: Dict[str, Dict[str, Any]] = {}

        # colas por zona (pedidos sin asignar a tanda todavía)
        self.zone_queues: Dict[str, deque] = {
            "NE": deque(), "NO": deque(), "SE": deque(), "SO": deque()
        }

        # cola de tandas esperando asignación a repartidor
        self.pending_tandas: deque = deque()

        # tandas activas: tanda_id -> dict(info)
        self.tandas: Dict[int, Dict[str, Any]] = {}

        # contador de tandas
        self._next_tanda_id = 1

        # historial de órdenes completas
        self.completed_orders: List[dict] = []

        # estadísticas globales
        self.stats = {
            "total_dispatched_orders": 0,
            "distance_by_delivery": {},  # delivery_id -> km
            "liters_by_delivery": {},  # delivery_id -> liters
            "orders_by_delivery": {},  # delivery_id -> count
        }

    # ------------------------
    # Registro y estado
    # ------------------------
    def register_delivery(self, delivery_id: str):
        if not delivery_id:
            return
        if delivery_id not in self.deliveries:
            self.deliveries[delivery_id] = {
                "status": "available",
                "assigned_tanda": None,
                "stats": {
                    "distance": 0.0,
                    "orders_delivered": 0
                }
            }

    def set_delivery_available(self, delivery_id: str):
        if delivery_id in self.deliveries:
            self.deliveries[delivery_id]["status"] = "available"
            self.deliveries[delivery_id]["assigned_tanda"] = None
            # intentar asignar tandas pendientes
            self._try_assign_tandas()

    def set_delivery_busy(self, delivery_id: str, tanda_id: int):
        if delivery_id in self.deliveries:
            self.deliveries[delivery_id]["status"] = "busy"
            self.deliveries[delivery_id]["assigned_tanda"] = tanda_id

    # ------------------------
    # Encolar orden (cliente)
    # ------------------------
    def enqueue_order(self, order: dict):
        """
        Recibe la orden (contiene lat, lon, id, code etc).
        Calcula zona y distancia, pone en la cola de zona,
        genera ETA estimado y si corresponde crea tanda.
        """
        lat = order.get("lat")
        lon = order.get("lon")
        if lat is None or lon is None:
            # no podemos procesar sin ubicación
            order["status"] = "pending_no_location"
            return order

        # distancia desde restaurante
        dist_km = round(haversine_km(RESTAURANT_COORDS[0], RESTAURANT_COORDS[1], lat, lon), 2)
        order["distance_km"] = dist_km

        # zona
        order_zone = zone_from_coords(lat, lon)
        order["zone"] = order_zone

        # timestamps
        order["enqueued_at"] = time.time()
        order["code"] = order.get("code") or generate_code()
        order["status"] = "pending"

        # estimación simple de tiempo: base + distance*KM_TO_MIN + cola_factor
        queue_len = len(self.zone_queues[order_zone])
        eta_min = int(BASE_PREP_MIN + dist_km * KM_TO_MIN + queue_len * 5)
        order["eta_min"] = eta_min

        # push a la cola de zona
        self.zone_queues[order_zone].append(order)

        # chequear si hay que crear una tanda
        self._maybe_create_tanda(order_zone)

        # intentar asignar tandas si hay repartidores
        self._try_assign_tandas()

        return order

    # ------------------------
    # Crear tanda desde cola de zona
    # ------------------------
    def _maybe_create_tanda(self, zone: str):
        """
        Crea tanda si:
         - la cola alcanzó TANDA_MAX pedidos
         - o el primer pedido lleva más de TANDA_MAX_WAIT_SECONDS esperando
        """
        q = self.zone_queues[zone]
        if not q:
            return

        first_enqueued = q[0]
        wait = time.time() - first_enqueued.get("enqueued_at", time.time())

        if len(q) >= TANDA_MAX or wait >= TANDA_MAX_WAIT_SECONDS:
            # crear tanda con hasta TANDA_MAX pedidos (FIFO)
            items = []
            for _ in range(min(TANDA_MAX, len(q))):
                items.append(q.popleft())

            tanda_id = self._next_tanda_id
            self._next_tanda_id += 1

            # construir árbol ordenado por distancia (BST mediana)
            items_sorted = sorted(items, key=lambda o: o["distance_km"])
            root = build_balanced_bst(items_sorted)
            # obtener recorrido inorder (que dará de más cercano a más lejano)
            ordered_list = []
            inorder_traversal(root, ordered_list)

            tanda = {
                "id": tanda_id,
                "zone": zone,
                "orders": ordered_list,  # orden a entregar: de más cercano a más lejano
                "created_at": time.time(),
                "assigned_to": None,
                "status": "pending"
            }
            self.tandas[tanda_id] = tanda
            self.pending_tandas.append(tanda_id)

    # ------------------------
    # Intentar asignar tandas a repartidores libres
    # ------------------------
    def _try_assign_tandas(self):
        if not self.pending_tandas:
            return

        # obtener lista de available deliveries
        available = [d for d, info in self.deliveries.items() if info["status"] == "available"]

        while available and self.pending_tandas:
            delivery_id = available.pop(0)
            tanda_id = self.pending_tandas.popleft()
            tanda = self.tandas.get(tanda_id)
            if not tanda:
                continue

            # asignar tanda al delivery
            tanda["assigned_to"] = delivery_id
            tanda["status"] = "assigned"
            tanda["assigned_at"] = time.time()
            self.deliveries[delivery_id]["status"] = "busy"
            self.deliveries[delivery_id]["assigned_tanda"] = tanda_id

            # initialize per-delivery tracking if missing
            self.stats["distance_by_delivery"].setdefault(delivery_id, 0.0)
            self.stats["orders_by_delivery"].setdefault(delivery_id, 0)

    # ------------------------
    # Verificar código y marcar entrega por parte del delivery
    # delivery_id envía el código del cliente para confirmar la entrega
    # ------------------------
    def verify_and_mark_delivered(self, delivery_id: str, code: str) -> bool:
        """
        Se espera que el repartidor tenga una tanda activa.
        Verificamos que el siguiente pedido en la tanda tenga ese código.
        Si corresponde, lo marcamos como entregado y avanzamos al siguiente.
        """
        if delivery_id not in self.deliveries:
            return False

        info = self.deliveries[delivery_id]
        tanda_id = info.get("assigned_tanda")
        if not tanda_id:
            return False

        tanda = self.tandas.get(tanda_id)
        if not tanda:
            return False

        # la tanda mantiene "orders" en orden de entrega (más cercano -> más lejano)
        if not tanda["orders"]:
            # no quedan órdenes (deberíamos liberar al delivery)
            tanda["status"] = "completed"
            self._finalize_tanda(tanda_id, delivery_id)
            return False

        current_order = tanda["orders"][0]
        if current_order.get("code", "").upper() != code.upper():
            return False

        # Coincide: marcar orden como entregada
        current_order["status"] = "delivered"
        current_order["delivered_at"] = time.time()
        current_order["delivered_by"] = delivery_id

        # actualizar estadísticas (distancia recorrida estimada y litros)
        dist = float(current_order.get("distance_km", 0.0))
        self.stats["total_dispatched_orders"] += 1
        self.stats["distance_by_delivery"].setdefault(delivery_id, 0.0)
        self.stats["distance_by_delivery"][delivery_id] += dist
        self.stats["orders_by_delivery"].setdefault(delivery_id, 0)
        self.stats["orders_by_delivery"][delivery_id] += 1
        liters = dist * LITERS_PER_KM
        self.stats["liters_by_delivery"].setdefault(delivery_id, 0.0)
        self.stats["liters_by_delivery"][delivery_id] += liters

        # mover orden al historial
        self.completed_orders.append(current_order)
        # removerla de la tanda (avanza al siguiente)
        tanda["orders"].pop(0)

        # Si ya no quedan órdenes en la tanda, finalizarla
        if not tanda["orders"]:
            tanda["status"] = "completed"
            self._finalize_tanda(tanda_id, delivery_id)
        else:
            # Si quedan órdenes, la tanda sigue activa; el delivery continúa
            pass

        return True

    # ------------------------
    # Finalizar tanda y liberar repartidor
    # ------------------------
    def _finalize_tanda(self, tanda_id: int, delivery_id: Optional[str]=None):
        tanda = self.tandas.get(tanda_id)
        if not tanda:
            return
        tanda["ended_at"] = time.time()
        tanda["status"] = "completed"
        # liberar delivery
        if delivery_id:
            if delivery_id in self.deliveries:
                self.deliveries[delivery_id]["status"] = "available"
                self.deliveries[delivery_id]["assigned_tanda"] = None
        # eliminar tanda de memoria (opcional mantener historial)
        # del self.tandas[tanda_id]
        # intentar asignar otras tandas pendientes
        self._try_assign_tandas()

    # ------------------------
    # Consultas / utilidades
    # ------------------------
    def get_pending_counts(self):
        return {z: len(q) for z, q in self.zone_queues.items()}

    def get_tanda_info(self, tanda_id: int) -> Optional[dict]:
        return self.tandas.get(tanda_id)

    def get_stats(self):
        return self.stats

# instancia global
DELIVERY_MANAGER = DeliveryManager()
