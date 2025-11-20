# utils/geo_calculator.py
from math import radians, sin, cos, sqrt, atan2

def haversine_km(lat1, lon1, lat2, lon2):
    """
    Calcula la distancia entre dos puntos geográficos usando la fórmula Haversine.
    Devuelve la distancia en kilómetros (float).
    """
    R = 6371.0  # radio de la Tierra en km

    lat1_r = radians(lat1)
    lon1_r = radians(lon1)
    lat2_r = radians(lat2)
    lon2_r = radians(lon2)

    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r

    a = (
        sin(dlat / 2) ** 2 +
        cos(lat1_r) * cos(lat2_r) * sin(dlon / 2) ** 2
    )
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c
