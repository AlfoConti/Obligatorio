# utils/cart_management.py
from datetime import datetime
import random, string
from utils.geo_calculator import haversine_km

def gen_code(n=6):
    import random, string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))

class CartManager:
    def __init__(self):
        self.users = {}    # phone -> user-state dict
        self.orders = {}   # order_id -> order
        self.order_counter = 1
        # restaurant coord (ajustar)
        self.restaurant_coord = (-34.9011, -56.1645)

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

    def reset_browse(self, phone):
        u = self.users[phone]
        u["page"] = 0
        u["filter"] = "Todos"
        u["sort_asc"] = True

    # cart ops
    def add_to_cart(self, phone, product_id, qty, details=""):
        user = self.users[phone]
        user["cart"].append({"product_id": product_id, "qty": qty, "details": details})
        return True

    def remove_from_cart(self, phone, idx):
        user = self.users[phone]
        try:
            user["cart"].pop(idx)
            return True
        except Exception:
            return False

    def cart_summary(self, phone):
        user = self.users[phone]
        lines = []
        tot = 0
        for i, it in enumerate(user["cart"], start=1):
            pid = it["product_id"]
            # product lookup will be done by catalog in main flow when formatting
            price = it.get("price", 0)
            sub = price * it["qty"]
            tot += sub
            lines.append(f"{i}) id:{pid} x{it['qty']} = ${sub} ({it['details']})")
        return ("\n".join(lines), tot)

    def create_order_from_cart(self, phone, lat=None, lon=None, product_lookup=None):
        # product_lookup: function to get product by id (catalog)
        user = self.users[phone]
        order_id = self.order_counter
        self.order_counter += 1
        items = []
        total = 0
        for it in user["cart"]:
            p = product_lookup(it["product_id"]) if product_lookup else {"price": it.get("price",0)}
            price = p.get("price", 0)
            items.append({"product": p, "qty": it["qty"], "details": it["details"]})
            total += price * it["qty"]
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
