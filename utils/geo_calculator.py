# utils/geo_calculator.py

import math


# ──────────────────────────────────────────────
# COORDENADAS DEL RESTAURANTE
# (Modificar según ubicación real)
# ──────────────────────────────────────────────
RESTAURANT_LAT = -34.9011
RESTAURANT_LON = -56.1645


# ──────────────────────────────────────────────
# Haversine: calcula distancia en kilómetros
# ──────────────────────────────────────────────
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Radio de la Tierra en km

    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = (math.sin(dlat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(dlon / 2) ** 2)

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return round(distance, 2)  # km redondeado


# ──────────────────────────────────────────────
# Tiempo estimado según distancia
# velocidad 30 km/h (delivery)
# ──────────────────────────────────────────────
def estimate_time(distance_km):
    if distance_km <= 0:
        return 1  # mínimo 1 minuto
    # tiempo en minutos
    time = (distance_km / 30) * 60
    return round(time)


# ──────────────────────────────────────────────
# Clasificar zona del pedido según coordenadas
# ──────────────────────────────────────────────
def classify_zone(lat, lon):
    """
    Divide la ciudad en 4 zonas a partir del restaurante:

      - NO (Noroeste)
      - NE (Noreste)
      - SO (Suroeste)
      - SE (Sureste)
    """

    north = lat > RESTAURANT_LAT
    east = lon > RESTAURANT_LON

    if north and east:
        return "NE"
    if north and not east:
        return "NO"
    if not north and east:
        return "SE"
    return "SO"


# ──────────────────────────────────────────────
# Función principal para usar desde main
# ──────────────────────────────────────────────
def process_location(user_lat, user_lon):
    """
    Devuelve un dict listo para enviar al bot de delivery:
    {
       "distance_km": 3.2,
       "time_min": 7,
       "zone": "SE"
    }
    """
    distance = calculate_distance(RESTAURANT_LAT, RESTAURANT_LON, user_lat, user_lon)
    time = estimate_time(distance)
    zone = classify_zone(user_lat, user_lon)

    return {
        "distance_km": distance,
        "time_min": time,
        "zone": zone
    }
