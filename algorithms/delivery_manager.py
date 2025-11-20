# algorithms/delivery_manager.py

import time
import random
import math
from typing import Dict, List, Optional
from structures.trees_and_queues import ZoneQueue, BSTree
from utils.cart_management import haversine_km  # reutilizamos el helper

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
        self.orders = orders  # lista de order dicts
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

        # tandas pendientes (id -> Tanda)
        self.tandas: Dict[int, Tanda] = {}
        self.next_tanda_id = 1

        # entregadores registrados
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
        zone = f"{lat_dir}{lon_dir}"  # NE, NO, SE, SO (pero queremos NO, NE, SO, SE)
        # fix letter order: lat+lon -> N/E => NE ; N/O => NO
        zone = zone.replace("EO", "E").replace("OO", "O")  # safety
        # Normalize to the four codes in our dict
        if zone == "NE" or zone == "EN":
            z = "NE"
        elif zone == "NO" or zone == "ON":
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
        if id_ in self.deliveries:
            return self.deliveries[id_]
        d = Delivery(id_, name)
        self.deliveries[id_] = d
        return d

    def enqueue_order(self, order: dict):
        """
        Espera recibir un 'order' que contenga lat, lon y user.number.
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
        # obtengo ruta inorder (de más cercano a más lejano)
        route = tanda.inorder_route()
        # Simular notificacion
        print(f"[NOTIFY] Delivery {delivery.id} ruta (in-order): {[o.get('user') for o in route]}")
        # aquí puedes integrar con whatsapp_service para enviar imagen de ruta y texto
        # por ejemplo: whatsapp_service.send_whatsapp_text(delivery_phone, "Tanda asignada...")
        # y enviar mapa: whatsapp_service.send_whatsapp_text(delivery_phone, "MAP_URL: ...")

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
        if current_order.get("code") != order_code:
            return False

        # marcar entregado: removemos el nodo actual de la lista de pedidos (reconstruimos BST sin el entregado)
        remaining = route[1:]  # drop first
        # actualizar tanda.orders y reconstruir BST
        tanda.orders = remaining
        tanda.bst.build_from_orders(remaining, key_fn=lambda o: o.get("distance_km", 0.0))

        # stats
        delivery.stats["orders_delivered"] += 1
        # sumar km recorrido: asumimos distancia desde restaurant hasta pedido (ida). double-check real route if needed
        distance = current_order.get("distance_km", 0.0)
        delivery.stats["km_traveled"] += distance * 2  # ida y vuelta aproximado
        delivery.stats["fuel_liters"] = delivery.stats["km_traveled"] / 10.0
        self.total_delivered += 1

        # notificar cliente y pedir calificacion (hook)
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

    # ------------------------
    # Utilitarios / reporting
    # ------------------------
    def report(self) -> dict:
        rep = {
            "total_delivered": self.total_delivered,
            "deliveries": {d.id: d.stats for d in self.deliveries.values()},
            "tandas_pending": list(self.pending_tandas_queue),
            "zones": {z: self.zones[z].size() for z in self.zones},
        }
        return rep

    def get_delivery_status(self, delivery_id: str) -> Optional[dict]:
        d = self.deliveries.get(delivery_id)
        if not d:
            return None
        return {
            "id": d.id,
            "state": d.state,
            "current_tanda": d.current_tanda_id,
            "stats": d.stats
        }

