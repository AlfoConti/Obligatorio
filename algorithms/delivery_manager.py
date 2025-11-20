# algorithms/delivery_manager.py

import time
import random
from typing import Dict, List, Optional
from structures.trees_and_queues import ZoneQueue, BSTree

# NOTA: haversine_km está en utils/cart_management.py
try:
    from utils.cart_management import haversine_km
except Exception:
    # fallback simple (si no existe la función)
    from math import radians, sin, cos, sqrt, atan2

    def haversine_km(lat1, lon1, lat2, lon2):
        R = 6371.0
        rlat1, rlon1, rlat2, rlon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = rlat2 - rlat1
        dlon = rlon2 - rlon1
        a = sin(dlat / 2) ** 2 + cos(rlat1) * cos(rlat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c


RANDOM_CODE_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


class Delivery:
    def __init__(self, id_: str, name: str = None):
        self.id = id_
        self.name = name or f"Delivery-{id_}"
        self.state = "available"  # available, busy
        self.current_tanda_id: Optional[int] = None
        self.stats = {
            "km_traveled": 0.0,
            "orders_delivered": 0,
            "fuel_liters": 0.0,
        }

    def assign_tanda(self, tanda_id: int):
        self.current_tanda_id = tanda_id
        self.state = "busy"

    def finish_tanda(self):
        self.current_tanda_id = None
        self.state = "available"


class Tanda:
    def __init__(self, id_: int, zone: str, orders: List[dict]):
        self.id = id_
        self.zone = zone
        self.orders = list(orders)  # lista de order dicts (copio)
        self.created_at = time.time()
        self.assigned_delivery: Optional[str] = None
        # Prepare BST structure (distance must be precomputed in orders as 'distance_km')
        self.bst = BSTree()
        self.bst.build_from_orders(self.orders, key_fn=lambda o: o.get("distance_km", 0.0))

    def inorder_route(self) -> List[dict]:
        return self.bst.inorder()


class DeliveryManager:
    def __init__(self, restaurant_lat: float, restaurant_lon: float):
        self.restaurant_lat = restaurant_lat
        self.restaurant_lon = restaurant_lon

        # 4 colas por zona
        self.zones: Dict[str, ZoneQueue] = {
            "NO": ZoneQueue("NO"),
            "NE": ZoneQueue("NE"),
            "SO": ZoneQueue("SO"),
            "SE": ZoneQueue("SE"),
        }

        # tandas (id -> Tanda)
        self.tandas: Dict[int, Tanda] = {}
        self.next_tanda_id = 1

        # repartidores registrados (id -> Delivery)
        self.deliveries: Dict[str, Delivery] = {}

        # cola de tandas pendientes (si no hay delivery available)
        self.pending_tandas_queue: List[int] = []

        # stats
        self.total_delivered = 0

    # ------------------------
    # Helpers zona / distancia
    # ------------------------
    def compute_distance_and_zone(self, lat: float, lon: float):
        d = haversine_km(self.restaurant_lat, self.restaurant_lon, lat, lon)
        # determinar cuadrante simple por lat/lon
        lat_dir = "N" if lat >= self.restaurant_lat else "S"
        lon_dir = "E" if lon >= self.restaurant_lon else "O"  # Oeste (O)
        zone = f"{lat_dir}{lon_dir}"  # NE, NO, SE, SO
        # Normalize to our 4 codes
        if zone == "NE":
            z = "NE"
        elif zone == "NO":
            z = "NO"
        elif zone == "SE":
            z = "SE"
        else:
            z = "SO"
        return d, z

    def _gen_order_code(self) -> str:
        return "".join(random.choices(RANDOM_CODE_CHARS, k=6))

    # ------------------------
    # Delivery management
    # ------------------------
    def register_delivery(self, id_: str, name: str = None):
        """
        Registra un repartidor. id_ puede ser el número de teléfono del repartidor
        o cualquier identificador único. Si ya existe, devuelve la instancia.
        """
        if id_ in self.deliveries:
            return self.deliveries[id_]
        d = Delivery(id_, name)
        self.deliveries[id_] = d
        return d

    def enqueue_order(self, order: dict):
        """
        Espera recibir un 'order' que contenga lat, lon y user (o user.number).
        - calcula distance_km y zone
        - añade code de verificación de 6 chars
        - encola en la zona correspondiente
        - intenta crear tanda si corresponde
        """
        lat = order.get("lat")
        lon = order.get("lon")
        if lat is None or lon is None:
            raise ValueError("order must include lat and lon")

        distance_km, zone = self.compute_distance_and_zone(lat, lon)
        order["distance_km"] = distance_km
        order["zone"] = zone
        order["code"] = self._gen_order_code()
        order["enqueued_at"] = time.time()
        order["status"] = "queued"

        zq = self.zones[zone]
        zq.enqueue(order)
        # intentar crear tanda
        self._maybe_create_tanda(zone)

        return order

    def _maybe_create_tanda(self, zone: str):
        zq = self.zones[zone]
        # criterio 1: 7 pedidos
        if zq.size() >= 7:
            orders = zq.dequeue_batch(7)
            self._create_and_assign_tanda(zone, orders)
            return

        # criterio 2: primer pedido espera > 45 minutos (2700s)
        first = zq.peek()
        if first:
            waited = time.time() - first.get("_enqueued_at", first.get("enqueued_at", time.time()))
            if waited >= (45 * 60):  # 45 min
                # dequeue all hasta crear tanda (puede ser menos de 7)
                orders = zq.dequeue_batch(zq.size())
                self._create_and_assign_tanda(zone, orders)
                return

    def _create_and_assign_tanda(self, zone: str, orders: List[dict]):
        tanda_id = self.next_tanda_id
        self.next_tanda_id += 1
        tanda = Tanda(tanda_id, zone, orders)
        self.tandas[tanda_id] = tanda

        # intentar asignar a delivery disponible
        available = [d for d in self.deliveries.values() if d.state == "available"]
        if available:
            d = random.choice(available)
            d.assign_tanda(tanda_id)
            tanda.assigned_delivery = d.id
            # Notificar al repartidor (simulado)
            print(f"[TANDA {tanda_id}] asignada al delivery {d.id} con {len(orders)} pedidos (zona {zone}).")
            # notificar via método hook (se puede integrar con whatsapp_service.send_whatsapp_text)
            self._notify_delivery_route(d, tanda)
        else:
            # encolar tanda pendiente
            self.pending_tandas_queue.append(tanda_id)
            print(f"[TANDA {tanda_id}] encolada (no hay delivery disponible).")

    def _notify_delivery_route(self, delivery: Delivery, tanda: Tanda):
        """
        Notifica al delivery la ruta (in-order) y envía un resumen.
        Intenta usar whatsapp_service si está instalado; si no, solo hace print().
        Se asume que delivery.id puede ser el teléfono del repartidor.
        """
        route = tanda.inorder_route()
        user_list = [o.get("user") or o.get("user_phone") or o.get("user_number") for o in route]
        msg = f"Tanda {tanda.id} asignada. {len(route)} pedidos. Ruta (más cercano→más lejano):\n" + \
              "\n".join([f"- {i+1}) {o.get('user', o.get('user_number',''))} ({o.get('distance_km',0):.2f} km)" for i, o in enumerate(route)])
        print(f"[NOTIFY] Delivery {delivery.id} ruta (in-order): {user_list}")
        print("[NOTIFY MESSAGE]:", msg)

        # intentar enviar por WhatsApp
        try:
            # import local para evitar ciclos en imports
            from whatsapp_service import send_whatsapp_text
            # si delivery.id es teléfono, lo usamos; si no, se puede mapear previamente
            recipient = delivery.id
            send_whatsapp_text(recipient, f"📦 *Tanda asignada* (ID: {tanda.id})\n{msg}")
            # si deseas enviar "mapa", aquí puedes construir una URL y usar otro helper (no incluido por defecto)
        except Exception as e:
            print("⚠️ _notify_delivery_route: no se pudo enviar WhatsApp:", e)

    # ------------------------
    # Consumir entrega (cuando delivery marca entrega y cliente da código)
    # ------------------------
    def verify_and_mark_delivered(self, delivery_id: str, order_code: str) -> bool:
        """
        Verifica si el código existe en la tanda actual del delivery.
        Si coincide con el pedido actual (primero en recorrido), lo marca como entregado,
        actualiza stats y avanza al siguiente.
        """
        delivery = self.deliveries.get(delivery_id)
        if not delivery or delivery.current_tanda_id is None:
            return False

        tanda = self.tandas.get(delivery.current_tanda_id)
        if not tanda:
            return False

        route = tanda.inorder_route()
        if not route:
            # tanda vacía -> finalizar
            delivery.finish_tanda()
            return False

        # primer pedido en inorder (actual)
        current_order = route[0]
        if str(current_order.get("code")).strip().upper() != str(order_code).strip().upper():
            return False

        # marcar entregado: removemos el nodo actual de la lista de pedidos (reconstruimos BST sin el entregado)
        remaining = route[1:]  # drop first
        # actualizar tanda.orders y reconstruir BST
        tanda.orders = remaining
        tanda.bst.build_from_orders(remaining, key_fn=lambda o: o.get("distance_km", 0.0))

        # stats
        delivery.stats["orders_delivered"] += 1
        distance = float(current_order.get("distance_km", 0.0))
        delivery.stats["km_traveled"] += distance * 2  # ida y vuelta aproximado
        delivery.stats["fuel_liters"] = delivery.stats["km_traveled"] / 10.0
        self.total_delivered += 1

        # notificar cliente y pedir calificacion (hook)
        try:
            from whatsapp_service import send_whatsapp_text
            client_phone = current_order.get("user") or current_order.get("user_number") or current_order.get("user_phone")
            if client_phone:
                send_whatsapp_text(client_phone, "✅ Tu pedido ha sido entregado. Por favor, califica el servicio del 1 al 5.")
        except Exception:
            print("[DELIVERED] no se pudo notificar por WhatsApp al cliente (puede que no exista send_whatsapp_text)")

        print(f"[DELIVERED] Order {current_order.get('id')} delivered by {delivery.id}")

        # si tanda queda vacía -> marcar delivery disponible y asignar nueva tanda pendiente si existe
        if not tanda.orders:
            delivery.finish_tanda()
            print(f"[TANDA {tanda.id}] finalizada por {delivery.id}")
            # asignar siguiente tanda pendiente si hay
            if self.pending_tandas_queue:
                next_tanda_id = self.pending_tandas_queue.pop(0)
                next_tanda = self.tandas.get(next_tanda_id)
                if next_tanda:
                    delivery.assign_tanda(next_tanda_id)
                    next_tanda.assigned_delivery = delivery.id
                    self._notify_delivery_route(delivery, next_tanda)
        return True
