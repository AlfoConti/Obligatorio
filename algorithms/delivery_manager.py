import math
from utils.geo_calculator import calculate_distance_km
from structures.data_models import Order, DeliveryInfo


class DeliveryManager:
    """
    Gestiona todo lo relacionado al delivery o retiro en local.
    Calcula distancias, tiempos estimados y costos.
    """

    BASE_DELIVERY_COST = 80
    COST_PER_KM = 25
    MAX_DISTANCE_KM = 20

    def __init__(self):
        pass

    # -----------------------------------------------------------
    # ✔ NUEVO: calcular costo + distancia + tiempo (para la UI)
    # -----------------------------------------------------------
    def get_delivery_summary(self, user_address: tuple, store_address: tuple):
        """
        Retorna un resumen completo para mostrar al usuario:
        distancia, costo total y tiempo estimado.
        """

        distance = calculate_distance_km(
            user_address[0], user_address[1],
            store_address[0], store_address[1]
        )

        if distance > self.MAX_DISTANCE_KM:
            return {
                "available": False,
                "message": f"Lo sentimos 😢 — solo entregamos hasta {self.MAX_DISTANCE_KM} km."
            }

        cost = self.BASE_DELIVERY_COST + (distance * self.COST_PER_KM)
        eta = self._estimate_time(distance)

        return {
            "available": True,
            "distance_km": round(distance, 2),
            "cost": round(cost, 2),
            "eta_minutes": eta
        }

    # -----------------------------------------------------------
    # ✔ NUEVO: texto formateado para enviar por WhatsApp
    # -----------------------------------------------------------
    def build_delivery_message(self, summary):
        """
        Genera el texto que se enviará cuando el usuario seleccione
        “Confirmar Delivery”.
        """
        if not summary["available"]:
            return summary["message"]

        return (
            f"🚚 *Resumen del Delivery*\n\n"
            f"📍 Distancia: *{summary['distance_km']} km*\n"
            f"⏱ Tiempo estimado: *{summary['eta_minutes']} minutos*\n"
            f"💰 Costo total: *${summary['cost']}*\n\n"
            f"¿Deseas confirmar tu pedido?"
        )

    # -----------------------------------------------------------
    # ✔ NUEVO: procesar confirmación del usuario
    # -----------------------------------------------------------
    def confirm_delivery(self, order: Order, summary, address_text):
        """
        Retorna toda la info lista para guardar en Order.
        """

        info = DeliveryInfo(
            method="delivery",
            cost=summary["cost"],
            distance=summary["distance_km"],
            estimated_time=summary["eta_minutes"],
            address=address_text
        )

        order.delivery_info = info
        return order

    # -----------------------------------------------------------
    # ✔ Para “Retiro en local”
    # -----------------------------------------------------------
    def confirm_store_pickup(self, order: Order):
        """
        El usuario retira en local.
        """
        info = DeliveryInfo(
            method="pickup",
            cost=0,
            distance=0,
            estimated_time=5,
            address="Local principal"
        )

        order.delivery_info = info
        return order

    # -----------------------------------------------------------
    # AUXILIAR: tiempo según distancia
    # -----------------------------------------------------------
    def _estimate_time(self, distance_km):
        """
        Tiempo estimado basado en distancia.
        """
        base_time = 10  # preparación
        travel_time = distance_km * 4  # minutos por km
        return int(base_time + travel_time)
