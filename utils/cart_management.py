# utils/cart_management.py
from datetime import datetime
import random, string
from utils.geo_calculator import haversine_km

def gen_code(n=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))

class CartManager:
    def __init__(self, product_lookup=None):
        self.users = {}
        self.orders = {}
        self.order_counter = 1
        self.restaurant_coord = (-34.9011, -56.1645)
        self.product_lookup = product_lookup

    def create_user_if_not_exists(self, phone):
        if phone not in self.users:
            self.users[phone] = {
                "created_at": datetime.utcnow(),
                "state": "idle",
                "page": 0,
                "filter": "Todos",
                "sort_asc": True,
                "cart": [],
                "temp_selection": None,
                "last_location": None
            }

    def get_user(self, phone):
        return self.users.get(phone)

    def add_to_cart(self, phone, product_id, qty, details=""):
        self.users[phone]["cart"].append({"product_id": product_id, "qty": qty, "details": details})
        return True

    def remove_from_cart(self, phone, idx):
        try:
            self.users[phone]["cart"].pop(idx)
            return True
        except Exception:
            return False

    def cart_summary(self, phone):
        user = self.users[phone]
        lines = []
        tot = 0
        for i, it in enumerate(user["cart"], start=1):
            p = self.product_lookup(it["product_id"]) if self.product_lookup else {"price": 0, "name": f"id{it['product_id']}"}
            price = p.get("price", 0)
            sub = price * it["qty"]
            tot += sub
            lines.append(f"{i}) {p.get('name','?')} x{it['qty']} = ${sub} ({it['details']})")
        return ("\n".join(lines), tot)

    def create_order_from_cart(self, phone, lat=None, lon=None):
        order_id = self.order_counter
        self.order_counter += 1
        user = self.users[phone]
        items = []
        total = 0
        for it in user["cart"]:
            p = self.product_lookup(it["product_id"]) if self.product_lookup else {"price": 0, "name": f"id{it['product_id']}"}
            items.append({"product": p, "qty": it["qty"], "details": it["details"]})
            total += p.get("price",0) * it["qty"]
        code = gen_code(6)
        dist = None
        if lat is not None and lon is not None:
            dist = round(haversine_km(self.restaurant_coord[0], self.restaurant_coord[1], lat, lon), 2)
        order = {
            "id": order_id,
            "phone": phone,
            "items": items,
            "total": total,
            "created_at": datetime.utcnow(),
            "status": "waiting",
            "code": code,
            "lat": lat,
            "lon": lon,
            "distance_km": dist
        }
        self.orders[order_id] = order
        user["cart"] = []
        return order
