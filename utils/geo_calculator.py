# utils/geo_calculator.py

import math

# 📍 Coordenadas de Referencia del Restaurante (Punto de Origen/Referencia 0,0)
# NOTA: Debes reemplazar estos valores con las coordenadas reales del restaurante.
RESTAURANT_LAT = -34.9011 # Ejemplo: Latitud de Montevideo (Sur es negativo)
RESTAURANT_LON = -56.1645 # Ejemplo: Longitud de Montevideo (Oeste es negativo)

# Constantes Geográficas
R = 6371  # Radio de la Tierra en kilómetros

# ====================================================================
# 1. Cálculo de Distancia (Fórmula de Haversine)
# ====================================================================

def calculate_distance(p1, p2):
    """
    Calcula la distancia de la Gran Círculo entre dos puntos (lat, lon) 
    usando la fórmula de Haversine.

    :param p1: Tupla (latitud, longitud) del punto 1 (ej: Restaurante).
    :param p2: Tupla (latitud, longitud) del punto 2 (ej: Cliente).
    :return: Distancia en kilómetros.
    """
    lat1, lon1 = p1
    lat2, lon2 = p2

    # Conversión de grados a radianes
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    # Fórmula de Haversine
    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance

# ====================================================================
# 2. Cálculo de Tiempo y Lógica de Negocio
# ====================================================================

# Velocidad de reparto asumida (ej: 20 km/h)
# NOTA: Esto es una simplificación. Un cálculo real usaría rutas y tráfico.
DELIVERY_SPEED_KMH = 20 

def estimate_delivery_time(distance_km):
    """
    Estima el tiempo de entrega basado en la distancia y una velocidad promedio.
    Añade un tiempo base de preparación/manejo.
    
    :param distance_km: Distancia calculada en kilómetros.
    :return: Tiempo estimado en minutos.
    """
    PREP_TIME_MIN = 15 # Tiempo base de preparación del pedido
    
    travel_time_hours = distance_km / DELIVERY_SPEED_KMH
    travel_time_minutes = travel_time_hours * 60
    
    total_time = PREP_TIME_MIN + travel_time_minutes
    return total_time

def calculate_fuel_spent(distance_km):
    """
    Calcula el combustible gastado (1 litro cada 10 km).
    """
    return distance_km / 10

# ====================================================================
# 3. Zonificación de Pedidos (4 Zonas)
# ====================================================================

def get_zone(client_location):
    """
    Determina la zona de reparto (NO, NE, SO, SE) basada en la ubicación 
    del cliente respecto al restaurante.

    :param client_location: Tupla (latitud, longitud) del cliente.
    :return: String con la zona ('NO', 'NE', 'SO', 'SE').
    """
    client_lat, client_lon = client_location
    
    # Diferencia de coordenadas respecto al restaurante
    lat_diff = client_lat - RESTAURANT_LAT
    lon_diff = client_lon - RESTAURANT_LON
    
    if lat_diff >= 0:
        # Hemisferio Norte (respecto al restaurante)
        if lon_diff >= 0:
            return "NE" # Noreste: Lat positiva, Lon positiva
        else:
            return "NO" # Noroeste: Lat positiva, Lon negativa
    else:
        # Hemisferio Sur (respecto al restaurante)
        if lon_diff >= 0:
            return "SE" # Sureste: Lat negativa, Lon positiva
        else:
            return "SO" # Suroeste: Lat negativa, Lon negativa