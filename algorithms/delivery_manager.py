import random
import string
import time
from collections import deque, defaultdict
from math import radians, sin, cos, sqrt, atan2
from typing import Dict, List, Optional, Any, Tuple


# -------------------------
# Utilidades
# -------------------------
def generate_code(length=6) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(random.choices(alphabet, k=length))


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    R = 6371.0
    rlat1, rlon1, rlat2, rlon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = rlat2 - rlat1
    dlon = rlon2 - rlon1
    a = sin(dlat / 2) ** 2 + cos(rlat1) * cos(rlat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


def zone_from_coords(rest_lat: float, rest_lon: float, lat: float, lon: float) -> str:
    """
    Divide el plano en 4 zonas respecto al restaurante:
    NO, NE, SO, SE (Noroeste, Noreste, Suroeste, Sureste)
    """
    if lat is None or lon is None:
        return "UNKNOWN"
    dy = lat - rest_lat
    dx = lon - rest_lon
    if dy >= 0 and dx < 0:
        return "NO"
    if dy >= 0 and dx >= 0:
        return "NE"
    if dy < 0 and dx < 0:
        return "SO"
    return "SE"


# -------------------------
# Nodo BST (para la tanda)
# -------------------------
class BSTNode:
    def __init__(self, order: dict, distance: float):
        self.order = order
        self.distance = distance
        self.left: Optional["BSTNode"] = None
        self.right: Optional["BSTNode"] = None


def build_bst_from_sorted(ordered: List[Tuple[dict, float]]) -> Optional[BSTNode]:
    """
    Construye un BST balanceado a partir de una lista ya ordenada por distancia.
    ordered: List of tuples (order_dict, distance)
    """
    if not ordered:
        return None
    mid = len(ordered) // 2
    node = BSTNode(ordered[mid][0], ordered[mid][1])
    node.left = build_bst_from_sorted(ordered[:mid])
    node.right = build_bst_from_sorted(ordered[mid + 1 :])
    return node


def inorder_list_from_bst(root: Optional[BSTNode]) -> List[dict]:
    res = []

    def _in(node: Optional[BSTNode]):
        if not node:
            return
        _in(node.left)
        res.append({"order": node.order, "distance": node.distance})
        _in(node.right)

    _in(root)
    return res


# -------------------------
# DeliveryManager
# -------------------------
class DeliveryManager:
    def __init__(self):
        # Repartidores registrados
        self.registered_deliveries: set[str] = set()

        # Estado de cada repartidor
        # delivery_id -> {
        #   'state': 'available'|'busy',
        #   'assigned_tanda': tanda_id or None,
        #   'delivered_count': int,
        #   'distance_km': float,
        #   'fuel_liters': float,
        #   'last_location': (lat, lon)  # where the driver is (starts at restaurant)
        # }
        self.deliveries: Dict[str, Dict[str, Any]] = {}

        # Colas por zona (cada zona -> deque of orders)
        self.zone_queues: Dict[str, deque] = {
            "NO": deque(),
            "NE": deque(),
            "SO": deque(),
            "SE": deque(),
            "UNKNOWN": deque(),
        }

        # Tandas creadas (id incremental)
        self.tanda_counter = 0
        # tanda_id -> tanda_info
        # tanda_info: {
        #   'zone': str,
        #   'orders': [order, ...],
        #   'bst_root': BSTNode,
        #   'inorder': [{'order':..., 'distance':...}, ...],
        #   'current_idx': int,
        #   'created_at': float,
        #   'delivery_id': optional
        # }
        self.tandas: Dict[int, Dict[str, Any]] = {}

        # Cola de tandas esperando asignación (FIFO)
        self.tanda_queue: deque = deque()

        # Parámetros
        self.max_per_tanda = 7
        self.max_wait_seconds = 45 * 60  # 45 minutos

        # Restaurante (punto de referencia)
        self.rest_lat: Optional[float] = None
        self.rest_lon: Optional[float] = None

        # Historial
        self.completed_orders: List[dict] = []

    # -------------------------
    # Configuración restaurante
    # -------------------------
    def set_restaurant_location(self, lat: float, lon: float):
        self.rest_lat = lat
        self.rest_lon = lon

    # -------------------------
    # Registro repartidor
    # -------------------------
    def register_delivery(self, delivery_id: str):
        if not delivery_id:
            return
        self.registered_deliveries.add(delivery_id)
        # Inicializar estado si no existe
        if delivery_id not in self.deliveries:
            self.deliveries[delivery_id] = {
                "state": "available",
                "assigned_tanda": None,
                "delivered_count": 0,
                "distance_km": 0.0,
                "fuel_liters": 0.0,
                "last_location": (self.rest_lat, self.rest_lon),
            }

    def is_registered(self, delivery_id: str) -> bool:
        return delivery_id in self.registered_deliveries

    # -------------------------
    # Encolar orden (cliente)
    # -------------------------
    def enqueue_order(self, order: dict) -> dict:
        """
        order: dict expected keys:
          - id (order id)
          - user (client id)
          - items, total, etc (optional)
          - lat, lon (recommended)
        Returns the order dict enriched with: code, status, zone, enqueued_at
        """
        code = generate_code()
        order["code"] = code
        order["status"] = "pending"
        order["enqueued_at"] = time.time()

        # Determine zone
        lat = order.get("lat")
        lon = order.get("lon")
        zone = "UNKNOWN"
        if self.rest_lat is not None and self.rest_lon is not None and lat is not None and lon is not None:
            zone = zone_from_coords(self.rest_lat, self.rest_lon, lat, lon)
        else:
            # if rest coords not set, try to default to UNKNOWN
            zone = "UNKNOWN"
        order["zone"] = zone

        # Append to zone queue
        q = self.zone_queues.get(zone, self.zone_queues["UNKNOWN"])
        q.append(order)

        # Try to create tanda if conditions met
        self._maybe_create_tanda(zone)

        # If there's tanda(s) in tanda_queue and some available deliveries, try assign
        self._try_assign_from_tanda_queue()

        return order

    # -------------------------
    # Revisar condiciones para crear tanda
    # -------------------------
    def _maybe_create_tanda(self, zone: str):
        q = self.zone_queues.get(zone)
        if not q:
            return

        # Condición 1: cola >= max_per_tanda
        if len(q) >= self.max_per_tanda:
            self._create_tanda_from_zone(zone)
            return

        # Condición 2: primer pedido espera > max_wait_seconds
        first = q[0]
        wait = time.time() - first.get("enqueued_at", time.time())
        if wait >= self.max_wait_seconds:
            self._create_tanda_from_zone(zone)
            return

    # -------------------------
    # Crear tanda (saca hasta max_per_tanda de la cola de zona)
    # -------------------------
    def _create_tanda_from_zone(self, zone: str):
        q = self.zone_queues.get(zone)
        if not q:
            return None

        orders = []
        for _ in range(min(self.max_per_tanda, len(q))):
            orders.append(q.popleft())

        # calcular distancias al restaurante
        enriched = []
        for o in orders:
            lat = o.get("lat")
            lon = o.get("lon")
            if self.rest_lat is not None and lat is not None:
                d = haversine_km(self.rest_lat, self.rest_lon, lat, lon)
            else:
                d = float("inf")
            enriched.append((o, d))

        # ordenar por distancia (asc)
        enriched_sorted = sorted(enriched, key=lambda x: x[1])

        # construir BST balanceado y obtener inorder (lista de entregas por orden asc)
        bst_root = build_bst_from_sorted(enriched_sorted)
        inorder = inorder_list_from_bst(bst_root)

        # crear tanda
        self.tanda_counter += 1
        tanda_id = self.tanda_counter
        tanda_info = {
            "id": tanda_id,
            "zone": zone,
            "orders": [entry["order"] for entry in inorder],
            "bst_root": bst_root,
            "inorder": inorder,  # list of {"order":..., "distance":...}
            "current_idx": 0,
            "created_at": time.time(),
            "delivery_id": None,
        }
        self.tandas[tanda_id] = tanda_info

        # Encolar la tanda (si no hay delivery disponible se quedará en tanda_queue)
        self.tanda_queue.append(tanda_id)

        # Intentar asignar la tanda inmediatamente
        self._try_assign_from_tanda_queue()

        return tanda_info

    # -------------------------
    # Intentar asignar tandas desde tanda_queue
    # -------------------------
    def _try_assign_from_tanda_queue(self):
        # while hay tandas y hay algún delivery registrado (sea available o no)
        while self.tanda_queue:
            tanda_id = self.tanda_queue[0]
            # buscar repartidor available
            available_id = None
            for d_id, st in self.deliveries.items():
                if st["state"] == "available":
                    available_id = d_id
                    break

            if available_id is not None:
                # asignar a available
                self.tanda_queue.popleft()
                self._assign_tanda_to_delivery(tanda_id, available_id)
                continue

            # Si no hay available, por letra: asignar aleatoriamente incluso si ocupado
            # (Se hace una sola asignación por tanda si hay repartidores registrados)
            if self.registered_deliveries:
                chosen = random.choice(list(self.registered_deliveries))
                self.tanda_queue.popleft()
                self._assign_tanda_to_delivery(tanda_id, chosen, force=True)
                continue

            # Si no hay repartidores registrados en absoluto, no podemos asignar
            break

    # -------------------------
    # Asignar tanda a delivery
    # -------------------------
    def _assign_tanda_to_delivery(self, tanda_id: int, delivery_id: str, force: bool = False):
        tanda = self.tandas.get(tanda_id)
        if not tanda:
            return False

        # Si delivery no registrado, registrar (comodín)
        if delivery_id not in self.deliveries:
            self.deliveries[delivery_id] = {
                "state": "available",
                "assigned_tanda": None,
                "delivered_count": 0,
                "distance_km": 0.0,
                "fuel_liters": 0.0,
                "last_location": (self.rest_lat, self.rest_lon),
            }
            self.registered_deliveries.add(delivery_id)

        delivery = self.deliveries[delivery_id]

        # Si delivery ya ocupado y no forzamos, no asignamos
        if delivery["state"] == "busy" and not force:
            return False

        # Asignación
        delivery["state"] = "busy"
        delivery["assigned_tanda"] = tanda_id
        # establecer last_location si no existe
        if delivery.get("last_location") is None:
            delivery["last_location"] = (self.rest_lat, self.rest_lon)

        tanda["delivery_id"] = delivery_id

        # Establecer active "current order" mapping para compatibilidad simple:
        current = tanda["inorder"][tanda["current_idx"]]["order"]
        # active_orders: map delivery -> current order (compat con versiones previas)
        # guardamos un snapshot simple: order id y code
        # Note: no se usa active_orders extensivamente aquí, la mecánica está en tanda.
        # Pero para compatibilidad mantenemos el atributo.
        # (Si es necesario, se puede exponer active_orders dict).
        # No retornamos nada.
        return True

    # -------------------------
    # Verificar código y marcar entregado
    # -------------------------
    def verify_and_mark_delivered(self, delivery_id: str, code: str) -> bool:
        """
        Se espera que delivery_id tenga una tanda asignada.
        El método verifica el código del pedido actualmente en curso por el delivery,
        y si coincide, marca como entregado y avanza al siguiente pedido de la tanda.

        Devuelve True si el código coincide y la entrega se marcó como completada.
        """
        if delivery_id not in self.deliveries:
            return False

        delivery = self.deliveries[delivery_id]
        tanda_id = delivery.get("assigned_tanda")
        if tanda_id is None:
            return False

        tanda = self.tandas.get(tanda_id)
        if not tanda:
            # inconsistencias: liberar estado
            delivery["assigned_tanda"] = None
            delivery["state"] = "available"
            return False

        idx = tanda["current_idx"]
        if idx >= len(tanda["inorder"]):
            # tanda ya completada, limpiar
            delivery["assigned_tanda"] = None
            delivery["state"] = "available"
            return False

        current_entry = tanda["inorder"][idx]
        order = current_entry["order"]
        expected_code = order.get("code", "").upper()

        if expected_code != (code or "").upper():
            return False

        # --- código válido: marcar como entregado ---
        order["status"] = "delivered"
        order["delivered_at"] = time.time()
        self.completed_orders.append(order)
        delivery["delivered_count"] = delivery.get("delivered_count", 0) + 1

        # calcular distancia recorrida desde last_location -> order location
        last_loc = delivery.get("last_location", (self.rest_lat, self.rest_lon))
        lat = order.get("lat")
        lon = order.get("lon")
        if lat is not None and lon is not None and last_loc[0] is not None:
            dist = haversine_km(last_loc[0], last_loc[1], lat, lon)
            if not (dist is None or dist != dist):  # check not NaN
                delivery["distance_km"] += dist
                delivery["fuel_liters"] = delivery["distance_km"] / 10.0  # 1 L per 10 km
            delivery["last_location"] = (lat, lon)
        else:
            # si no hay coords, no sumamos distancia
            dist = 0.0

        # Avanzar al siguiente pedido en la tanda
        tanda["current_idx"] += 1

        # Si quedan pedidos, actualizamos (current order será el siguiente)
        if tanda["current_idx"] < len(tanda["inorder"]):
            next_order = tanda["inorder"][tanda["current_idx"]]["order"]
            # guardamos/actualizamos si se necesita
            # (no hacemos notificaciones aquí; la integración externa debería notificar al delivery)
        else:
            # tanda completada
            tanda["completed_at"] = time.time()
            # liberar delivery
            delivery["assigned_tanda"] = None
            delivery["state"] = "available"
            tanda["delivery_id"] = None
            # opcional: reasignar nuevas tandas en cola
            self._try_assign_from_tanda_queue()

        return True

    # -------------------------
    # Método utilitario: obtener estado actual (para consola/testing)
    # -------------------------
    def status_overview(self) -> Dict[str, Any]:
        """Devuelve un snapshot con métricas y colas (útil para debugging)."""
        overview = {
            "registered_deliveries": list(self.registered_deliveries),
            "deliveries": self.deliveries,
            "zone_queue_lengths": {z: len(q) for z, q in self.zone_queues.items()},
            "tanda_queue": list(self.tanda_queue),
            "tandas_active": {
                tid: {
                    "zone": t["zone"],
                    "total_orders": len(t["orders"]),
                    "current_idx": t["current_idx"],
                    "delivery_id": t["delivery_id"],
                }
                for tid, t in self.tandas.items()
            },
            "completed_orders_count": len(self.completed_orders),
        }
        return overview

    # -------------------------
    # Métricas finales (console report)
    # -------------------------
    def report(self) -> Dict[str, Any]:
        """Reporte resumido para mostrar en consola (total entregados, distancias, combustible)."""
        per_delivery = {}
        total_delivered = len(self.completed_orders)
        total_distance = 0.0
        total_fuel = 0.0
        for d_id, st in self.deliveries.items():
            per_delivery[d_id] = {
                "delivered_count": st.get("delivered_count", 0),
                "distance_km": round(st.get("distance_km", 0.0), 2),
                "fuel_liters": round(st.get("fuel_liters", 0.0), 2),
            }
            total_distance += st.get("distance_km", 0.0)
            total_fuel += st.get("fuel_liters", 0.0)

        report = {
            "total_orders_delivered": total_delivered,
            "total_distance_km": round(total_distance, 2),
            "total_fuel_liters": round(total_fuel, 2),
            "per_delivery": per_delivery,
            "clients_and_orders": [
                {"order_id": o.get("id"), "client": o.get("user"), "items": o.get("items"), "status": o.get("status")}
                for o in self.completed_orders
            ],
        }
        return report


# Instancia global
DELIVERY_MANAGER = DeliveryManager()