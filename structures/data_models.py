# structures/data_models.py

from dataclasses import dataclass


# ──────────────────────────────────────────────
# ÍTEM DEL CARRITO
# ──────────────────────────────────────────────
@dataclass
class CartItem:
    id: str          # ID del producto (desde catalog.json)
    name: str        # Nombre del producto
    price: float     # Precio unitario
    quantity: int    # Cantidad seleccionada

    def get_subtotal(self):
        return round(self.price * self.quantity, 2)


# ──────────────────────────────────────────────
# PEDIDO DE DELIVERY
# ──────────────────────────────────────────────
@dataclass
class DeliveryOrder:
    user_id: str
    order_code: str
    zone: str            # NE / NO / SE / SO
    latitude: float
    longitude: float
    cart_items: list     # lista de CartItem
    total_amount: float
    distance_km: float
    estimated_time: int  # minutos

    def summary_text(self):
        """
        Devuelve un texto bonito para enviar al WhatsApp del cliente.
        """
        items_text = "\n".join(
            [f"- {item.name} x{item.quantity} → ${item.get_subtotal()}"
             for item in self.cart_items]
        )

        return (
            f"🧾 *Resumen del pedido {self.order_code}*\n\n"
            f"{items_text}\n\n"
            f"📍 Zona: {self.zone}\n"
            f"📏 Distancia: {self.distance_km} km\n"
            f"⏱ Tiempo estimado: {self.estimated_time} min\n"
            f"💵 Total: ${self.total_amount}"
        )
