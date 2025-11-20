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
RESTAURANT_COORDS = (-31.383640, -57.960620)  # Ubicación real del restaurante
TANDA_MAX = 7
TANDA_MAX_WAIT_SECONDS = 45 * 60  # 45 minutos
KM_TO_MIN = 2.0  # convertir km a minutos estimados
BASE_PREP_MIN = 10  # tiempo base
LITERS_PER_KM = 0.1  # 1 L cada 10 km -> 0.1 L/km

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
# BST helper
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
        self.deliveries: Dict[str, Dict[str, Any]] = {}
        self.zone_queues: Dict[str, deque] = {
            "NE": deque(), "NO": deque(), "SE": deque(), "SO": deque()
        }
        self.pending_tandas: deque = deque()
        self.tandas: Dict[int, Dict[str, Any]] = {}
        self._next_tanda_id = 1
        self.completed_orders: List[dict] = []
        self.stats = {
            "total_dispatched_orders": 0,
            "distance_by_delivery": {},
            "liters_by_delivery": {},
            "orders_by_delivery": {},
        }

    # ------------------------
    # Registro
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
                    "orders_delivered": 0,
                }
            }

    def set_delivery_available(self, delivery_id: str):
        if delivery_id in self.deliveries:
            self.deliveries[delivery_id]["status"] = "available"
            self.deliveries[delivery_id]["assigned_tanda"] = None
            self._try_assign_tandas()

    def set_delivery_busy(self, delivery_id: str, tanda_id: int):
        if delivery_id in self.deliveries:
            self.deliveries[delivery_id]["status"] = "busy"
            self.deliveries[delivery_id]["assigned_tanda"] = tanda_id

    # ------------------------
    # Encolar orden
    # ------------------------
    def enqueue_order(self, order: dict):
        lat = order.get("lat")
        lon = order.get("lon")

        if lat is None or lon is None:
            order["status"] = "pending_no_location"
            return order

        dist_km = round(haversine_km(
            RESTAURANT_COORDS[0], RESTAURANT_COORDS[1], lat, lon
        ), 2)
        order["distance_km"] = dist_km

        order_zone = zone_from_coords(lat, lon)
        order["zone"] = order_zone

        order["enqueued_at"] = time.time()
        order["code"] = order.get("code") or generate_code()
        order["status"] = "pending"

        queue_len = len(self.zone_queues[order_zone])
        order["eta_min"] = int(BASE_PREP_MIN + dist_km * KM_TO_MIN + queue_len * 5)

        self.zone_queues[order_zone].append(order)

        self._maybe_create_tanda(order_zone)
        self._try_assign_tandas()

        return order

    # ------------------------
    # Crear tanda
    # ------------------------
    def _maybe_create_tanda(self, zone: str):
        q = self.zone_queues[zone]
        if not q:
            return

        wait = time.time() - q[0].get("enqueued_at", time.time())

        if len(q) >= TANDA_MAX or wait >= TANDA_MAX_WAIT_SECONDS:

            items = []
            for _ in range(min(TANDA_MAX, len(q))):
                items.append(q.popleft())

            tanda_id = self._next_tanda_id
            self._next_tanda_id += 1

            items_sorted = sorted(items, key=lambda o: o["distance_km"])
            root = build_balanced_bst(items_sorted)

            ordered_list = []
            inorder_traversal(root, ordered_list)

            tanda = {
                "id": tanda_id,
                "zone": zone,
                "orders": ordered_list,
                "created_at": time.time(),
                "assigned_to": None,
                "status": "pending"
            }

            self.tandas[tanda_id] = tanda
            self.pending_tandas.append(tanda_id)

    # ------------------------
    # Asignar tandas
    # ------------------------
    def _try_assign_tandas(self):
        if not self.pending_tandas:
            return

        available = [d for d, info in self.deliveries.items() if info["status"] == "available"]

        while available and self.pending_tandas:
            delivery_id = available.pop(0)
            tanda_id = self.pending_tandas.popleft()

            tanda = self.tandas.get(tanda_id)
            if not tanda:
                continue

            tanda["assigned_to"] = delivery_id
            tanda["status"] = "assigned"
            tanda["assigned_at"] = time.time()

            self.deliveries[delivery_id]["status"] = "busy"
            self.deliveries[delivery_id]["assigned_tanda"] = tanda_id

            self.stats["distance_by_delivery"].setdefault(delivery_id, 0.0)
            self.stats["orders_by_delivery"].setdefault(delivery_id, 0)

    # ------------------------
    # Verificar entrega
    # ------------------------
    def verify_and_mark_delivered(self, delivery_id: str, code: str) -> bool:
        if delivery_id not in self.deliveries:
            return False

        info = self.deliveries[delivery_id]
        tanda_id = info.get("assigned_tanda")

        if not tanda_id:
            return False

        tanda = self.tandas.get(tanda_id)
        if not tanda or not tanda["orders"]:
            return False

        current_order = tanda["orders"][0]

        if current_order.get("code", "").upper() != code.upper():
            return False

        current_order["status"] = "delivered"
        current_order["delivered_at"] = time.time()
        current_order["delivered_by"] = delivery_id

        dist = float(current_order.get("distance_km", 0.0))
        self.stats["total_dispatched_orders"] += 1
        self.stats["distance_by_delivery"][delivery_id] += dist
        self.stats["orders_by_delivery"][delivery_id] += 1

        liters = dist * LITERS_PER_KM
        self.stats["liters_by_delivery"].setdefault(delivery_id, 0.0)
        self.stats["liters_by_delivery"][delivery_id] += liters

        self.completed_orders.append(current_order)
        tanda["orders"].pop(0)

        if not tanda["orders"]:
            tanda["status"] = "completed"
            self._finalize_tanda(tanda_id, delivery_id)

        return True

    # ------------------------
    # Finalizar tanda
    # ------------------------
    def _finalize_tanda(self, tanda_id: int, delivery_id: Optional[str] = None):
        tanda = self.tandas.get(tanda_id)
        if not tanda:
            return

        tanda["ended_at"] = time.time()
        tanda["status"] = "completed"

        if delivery_id and delivery_id in self.deliveries:
            self.deliveries[delivery_id]["status"] = "available"
            self.deliveries[delivery_id]["assigned_tanda"] = None

        self._try_assign_tandas()

    # ------------------------
    # Consultas
    # ------------------------
    def get_pending_counts(self):
        return {z: len(q) for z, q in self.zone_queues.items()}

    def get_tanda_info(self, tanda_id: int) -> Optional[dict]:
        return self.tandas.get(tanda_id)

    def get_stats(self):
        return self.stats


# instancia global
DELIVERY_MANAGER = DeliveryManager()
