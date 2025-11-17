import math


# Coordenadas del restaurante (ejemplo)
# Cambialas por las reales si querés.
RESTAURANT_LAT = -34.9011
RESTAURANT_LON = -56.1645


# -----------------------------------------------------------
# Fórmula de Haversine
# -----------------------------------------------------------
def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calcula la distancia en kilómetros entre dos puntos usando Haversine.
    """
    R = 6371  # kilómetros

    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (math.sin(dlat / 2) ** 2 +
         math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)

    c = 2 * math.asin(math.sqrt(a))

    return R * c  # distancia en KM


# -----------------------------------------------------------
# Tiempo estimado según velocidad promedio
# -----------------------------------------------------------
def calculate_eta(distance_km, speed_kmh=25):
    """
    Calcula tiempo estimado en minutos según velocidad promedio.
    Default: 25 km/h (delivery moto).
    """
    if distance_km <= 0:
        return 5  # mínimo

    hours = distance_km / speed_kmh
    minutes = int(hours * 60)
    return max(minutes, 5)


# -----------------------------------------------------------
# Función principal llamada desde main.py
# -----------------------------------------------------------
def process_delivery_coordinates(user_lat, user_lon):
    """
    Recibe latitud y longitud del cliente.
    Devuelve dict con distancia, tiempo estimado y texto.
    """

    distance = calculate_distance(RESTAURANT_LAT, RESTAURANT_LON, user_lat, user_lon)
    eta = calculate_eta(distance)

    result = {
        "distance_km": round(distance, 2),
        "eta_minutes": eta,
        "text": (
            f"📍 *Ubicación recibida*\n"
            f"Distancia al restaurante: *{round(distance, 2)} km*\n"
            f"⏱ Tiempo estimado de entrega: *{eta} minutos*"
        )
    }

    return result
