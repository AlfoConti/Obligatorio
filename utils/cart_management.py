# utils/cart_management.py
import random
import math
import time

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    from math import radians, sin, cos, sqrt, atan2
    rlat1, rlon1, rlat2, rlon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = rlat2 - rlat1
    dlon = rlon2 - rlon1
    a = sin(dlat/2)**2 + cos(rlat1)*cos(rlat2)*sin(dlon/2)**2
    c = 2*atan2(sqrt(a), sqrt(1-a))
    return R * c

class CartManager:
    def __init__(self, product_lookup):
        # product_lookup: función(product_id) -> producto dict
        self.product_lookup = product_lookup
        self.users = {}  # phone -> state dict
        self.orders = []  # lista de órdenes creadas

    def create_user_if_not_exists(self, phone):
        if phone not in self.users:
            self.users[phone] = {
                "phone": phone,
                "cart": [],  # list of {product_id, qty, details}
                "state": "idle",
                "page": 0,
                "filter": None,
                "sort_asc": True,
            }

    def get_user(self, phone):
        self.create_user_if_not_exists(phone)
        return self.users[phone]

    def add_to_cart(self, phone, product_id, qty, details=""):
        self.create_user_if_not_exists(phone)
        prod = self.product_lookup(product_id)
        if not prod:
            return False
        self.users[phone]['cart'].append({"product": prod, "qty": int(qty), "details": details})
        return True

    def cart_summary(self, phone):
        u = self.get_user(phone)
        lines = []
        total = 0.0
        for idx, item in enumerate(u['cart'], start=1):
            sub = float(item['product'].get('price', 0)) * int(item['qty'])
            lines.append(f"{idx}) {item['product']['name']} x{item['qty']} - ${sub} ({item['details']})")
            total += sub
        return ("\n".join(lines), round(total,2))

    def remove_from_cart(self, phone, index):
        u = self.get_user(phone)
        if 0 <= index < len(u['cart']):
            u['cart'].pop(index)
            return True
        return False

    def create_order_from_cart(self, phone, lat, lon):
        u = self.get_user(phone)
        lines, total = self.cart_summary(phone)
        order_id = len(self.orders) + 1
        code = ''.join(random.choices('ABCDEFGHJKLMNPQRSTUVWXYZ23456789', k=6))
        items = [{"id": item['product']['id'], "name": item['product']['name'], "qty": item['qty'], "price": item['product'].get('price',0)} for item in u['cart']]
        # calculate distance from restaurant (to be set outside)
        order = {
            "id": order_id,
            "user": phone,
            "items": items,
            "total": total,
            "code": code,
            "lat": lat,
            "lon": lon,
            "created_at": time.time(),
            "status": "queued"
        }
        self.orders.append(order)
        # clear cart
        u['cart'] = []
        return order
