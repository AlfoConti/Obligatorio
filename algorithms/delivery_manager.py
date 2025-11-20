# algorithms/delivery_manager.py
from collections import deque
import string
import random


def generate_code(length=6):
    """Genera un código alfanumérico para las órdenes."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


class DeliveryManager:
    """
    Sistema de delivery:
    - Registra repartidores
    - Encola pedidos
    - Asigna pedidos al repartidor disponible
    - Verifica códigos de entrega
    """

    def __init__(self):
        self.registered_deliveries = set()          # teléfonos de repartidores
        self.pending_orders = deque()               # pedidos pendientes
        self.active_orders = {}                     # delivery_id -> order
        self.completed_orders = []                  # historial

    # -------------------------------------------------------------------
    # REGISTRO
    # -------------------------------------------------------------------
    def register_delivery(self, delivery_id: str):
        """Registra un repartidor por su número de teléfono."""
        if delivery_id:
            self.registered_deliveries.add(delivery_id)

    def is_registered(self, delivery_id: str) -> bool:
        return delivery_id in self.registered_deliveries

    # -------------------------------------------------------------------
    # ENCOLAR ORDEN
    # -------------------------------------------------------------------
    def enqueue_order(self, order: dict):
        """
        Añade un pedido a la cola y asigna automáticamente al siguiente
        repartidor libre.
        """
        order_code = generate_code()
        order["code"] = order_code
        order["status"] = "pending"

        self.pending_orders.append(order)

        # intentar asignar automáticamente
        self.assign_orders()

        return order

    # -------------------------------------------------------------------
    # ASIGNACIÓN AUTOMÁTICA
    # -------------------------------------------------------------------
    def assign_orders(self):
        """
        Asigna pedidos pendientes a repartidores libres.
        """
        if not self.pending_orders:
            return

        for delivery_id in list(self.registered_deliveries):
            if delivery_id not in self.active_orders:
                if self.pending_orders:
                    new_order = self.pending_orders.popleft()
                    new_order["status"] = "assigned"
                    new_order["delivery_id"] = delivery_id
                    self.active_orders[delivery_id] = new_order

    # -------------------------------------------------------------------
    # VERIFICACIÓN DE ENTREGA
    # -------------------------------------------------------------------
    def verify_and_mark_delivered(self, delivery_id: str, code: str):
        """
        El repartidor envía el código → se verifica → se marca entregado.
        """
        if delivery_id not in self.active_orders:
            return False

        order = self.active_orders[delivery_id]

        if order["code"] != code.upper():
            return False

        # marcar como completada
        order["status"] = "delivered"
        self.completed_orders.append(order)
        del self.active_orders[delivery_id]

        # reasignar siguiente
        self.assign_orders()
        return True


# Instancia global para usar en main.py
DELIVERY_MANAGER = DeliveryManager()
