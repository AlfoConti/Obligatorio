# algorithms/delivery_manager.py
import math
import random
from collections import deque

class DeliveryManager:
    def __init__(self, restaurant_coord=(-34.9011, -56.1645)):
        self.restaurant_coord = restaurant_coord
        # four queues for zones: NO, NE, SO, SE
        self.queues = {
            "NO": deque(),
            "NE": deque(),
            "SO": deque(),
            "SE": deque()
        }
        self.tandas_queue = deque()
        self.repartidores = []  # list of repartidor dicts {id, state:'available'|'busy', stats...}
        self.tandas = []  # tandas creadas

    def _zone_for_coord(self, lat, lon):
        lat0, lon0 = self.restaurant_coord
        # simple quadrant logic
        if lat >= lat0 and lon < lon0:
            return "NO"
        if lat >= lat0 and lon >= lon0:
            return "NE"
        if lat < lat0 and lon < lon0:
            return "SO"
        return "SE"

    def enqueue_order(self, order):
        zone = self._zone_for_coord(order['lat'], order['lon'])
        self.queues[zone].append(order)
        return zone

    def process_all_queues_and_create_tandas(self, orders_list=None):
        """
        Revisa cada cola; si tiene 7 pedidos o si el primer pedido tiene >45 min (omito tiempo real en el prototipo)
        crea una tanda. Retorna número de tandas creadas en esta pasada.
        """
        created = 0
        for zone, q in self.queues.items():
            if len(q) >= 7:
                self._create_tanda_from_queue(zone)
                created += 1
            elif len(q) > 0:
                # simplified: si hay cualquiera, podemos crear tanda (para demo)
                self._create_tanda_from_queue(zone)
                created += 1
        return created

    def _create_tanda_from_queue(self, zone):
        q = self.queues[zone]
        if not q:
            return None
        # tomar hasta 7 pedidos
        items = []
        for _ in range(min(7, len(q))):
            items.append(q.popleft())
        tanda = {
            "id": len(self.tandas) + 1,
            "zone": zone,
            "orders": items,
            "assigned_to": None,
            "status": "created"
        }
        # asignar repartidor disponible si existe
        for r in self.repartidores:
            if r.get("state") == "available":
                tanda["assigned_to"] = r["id"]
                r["state"] = "busy"
                break
        # si no hay repartidor disponible, encolamos la tanda
        if tanda["assigned_to"] is None:
            self.tandas_queue.append(tanda)
        else:
            tanda["status"] = "assigned"
        self.tandas.append(tanda)
        return tanda

    # funciones de ayuda para testing
    def add_repartidor(self, rep_id):
        self.repartidores.append({"id": rep_id, "state": "available", "delivered": 0, "distance": 0.0})

    def assign_queued_tandas(self):
        # intentar asignar tandas en espera a repartidores (incluso ocupados en tu lógica original, aquí asigna solo a available)
        assigned = 0
        for _ in range(len(self.tandas_queue)):
            tanda = self.tandas_queue.popleft()
            for r in self.repartidores:
                if r["state"] == "available":
                    tanda["assigned_to"] = r["id"]
                    tanda["status"] = "assigned"
                    r["state"] = "busy"
                    assigned += 1
                    break
            if tanda["assigned_to"] is None:
                self.tandas_queue.append(tanda)
        return assigned
