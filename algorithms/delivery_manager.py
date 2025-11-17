# algorithms/delivery_manager.py
from datetime import datetime, timedelta
from utils.geo_calculator import haversine_km

class DeliveryManager:
    def __init__(self, restaurant_coord=(-34.9011, -56.1645)):
        self.queues = {"NO": [], "NE": [], "SO": [], "SE": []}
        self.tandas = {}  # id -> dict
        self.tanda_counter = 1
        self.deliveries = {}  # id -> {available, phone}
        self.tanda_queue = []
        self.restaurant_coord = restaurant_coord

    def get_zone(self, lat, lon):
        rlat, rlon = self.restaurant_coord
        if lat >= rlat and lon < rlon:
            return "NO"
        if lat >= rlat and lon >= rlon:
            return "NE"
        if lat < rlat and lon < rlon:
            return "SO"
        return "SE"

    def enqueue_order(self, order):
        lat, lon = order.get("lat"), order.get("lon")
        if lat is None or lon is None:
            return False
        zone = self.get_zone(lat, lon)
        self.queues[zone].append(order["id"])
        return True

    def check_and_create_tanda_for_zone(self, zone, orders_dict):
        q = self.queues[zone]
        if not q:
            return None
        first_order = orders_dict[q[0]]
        now = datetime.utcnow()
        if len(q) >= 7 or (now - first_order["created_at"]) > timedelta(minutes=45):
            take = q[:7]
            self.queues[zone] = q[len(take):]
            tid = self.tanda_counter
            self.tanda_counter += 1
            self.tandas[tid] = {"orders": take, "delivery_id": None, "created_at": datetime.utcnow(), "route": []}
            for oid in take:
                orders_dict[oid]["status"] = "assigned"
            return tid
        return None

    def process_all_queues_and_create_tandas(self, orders_dict):
        created = []
        for z in list(self.queues.keys()):
            tid = self.check_and_create_tanda_for_zone(z, orders_dict)
            if tid:
                created.append(tid)
                self.assign_tanda_to_delivery(tid, orders_dict)
        while self.tanda_queue:
            tid = self.tanda_queue.pop(0)
            self.assign_tanda_to_delivery(tid, orders_dict)
        return created

    def assign_tanda_to_delivery(self, tanda_id, orders_dict):
        # try find available delivery
        for did, d in self.deliveries.items():
            if d.get("available", True):
                d["available"] = False
                d["assigned_tanda_id"] = tanda_id
                self.tandas[tanda_id]["delivery_id"] = did
                order_ids = self.tandas[tanda_id]["orders"]
                order_ids_sorted = sorted(order_ids, key=lambda oid: orders_dict[oid].get("distance_km", 0))
                self.tandas[tanda_id]["route"] = order_ids_sorted
                return did
        self.tanda_queue.append(tanda_id)
        return None

    def register_delivery(self, phone):
        did = len(self.deliveries) + 1
        self.deliveries[did] = {"available": True, "phone": phone, "assigned_tanda_id": None}
        return did
