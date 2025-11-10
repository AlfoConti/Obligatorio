# delivery_manager.py

import time
import random
import string
from collections import deque # Se usa deque para implementar las Colas si no hay una clase Cola específica.

# ⚙️ Importaciones de Módulos de Estructuras y Lógica
from structures.trees_and_queues import BinarySearchTree # Implementación del ABB
from structures.data_models import Order, Delivery, get_all_deliveries, update_delivery_state # Modelos y acceso a Deliverys
from utils.geo_calculator import get_zone, calculate_distance # Lógica de zonificación y distancia

# ====================================================================
# 1. Almacenamiento Global de Pedidos y Deliverys
# NOTA: En un proyecto real, estas estructuras serían persistentes (BD, Redis, etc.)
# Aquí las mantenemos en memoria para el prototipo.
# ====================================================================

# 4 Colas FIFO para almacenar pedidos por zona
ORDER_QUEUES = {
    "NO": deque(), # Noroeste
    "NE": deque(), # Noreste
    "SO": deque(), # Suroeste
    "SE": deque(), # Sureste
}

# Cola para tandas en espera de un delivery disponible
TANDA_WAITING_QUEUE = deque()

# Constantes para la lógica de la tanda
MAX_PEDIDOS_TANDA = 7
MAX_TIEMPO_ESPERA = 45 * 60 # 45 minutos en segundos

# ====================================================================
# 2. Funciones de Ayuda
# ====================================================================

def generate_verification_code():
    """Genera un código aleatorio de 6 caracteres."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def get_available_delivery():
    """Busca un delivery disponible."""
    all_deliveries = get_all_deliveries() # Asume esta función de data_models
    for delivery in all_deliveries:
        if delivery.state == "available":
            return delivery
    return None

# ====================================================================
# 3. Gestión de Pedidos (Almacenamiento y Zonificación)
# ====================================================================

def place_new_order(order_data, client_location):
    """
    Recibe un nuevo pedido, calcula la zona y lo encola.
    
    :param order_data: Objeto o dict con los detalles del pedido (carrito, total, etc.)
    :param client_location: (lat, lon) del cliente.
    :return: Objeto Order creado.
    """
    # Asume que el restaurante es el origen (0,0) para la zonificación
    restaurant_location = (0.0, 0.0) # Obtener de config.py
    
    # Calcular distancia y asignar código
    distance_km = calculate_distance(restaurant_location, client_location)
    verification_code = generate_verification_code()
    
    # Crear el objeto Pedido (Order)
    new_order = Order(
        order_id=random.randint(1000, 9999), # ID temporal
        products=order_data.get('products'),
        total=order_data.get('total'),
        client_location=client_location,
        distance=distance_km,
        verification_code=verification_code,
        timestamp=time.time() # Tiempo de inicio de espera
    )
    
    # Determinar la zona y encolar
    zone = get_zone(client_location)
    ORDER_QUEUES[zone].append(new_order)
    
    # Intentar procesar la cola inmediatamente para ver si se forma una tanda
    check_and_create_tandas(zone)
    
    return new_order

# ====================================================================
# 4. Lógica de Tandas y Asignación (Colas y Disponibilidad)
# ====================================================================

def create_tanda_from_queue(zone_queue):
    """Desencola y crea un objeto Tanda con los pedidos seleccionados."""
    tanda_orders = []
    # Desencolar todos los pedidos, o hasta el máximo (7)
    for _ in range(min(len(zone_queue), MAX_PEDIDOS_TANDA)):
        tanda_orders.append(zone_queue.popleft())
        
    return tanda_orders

def check_and_create_tandas(zone):
    """Verifica si la cola de una zona cumple las condiciones para formar una tanda."""
    
    queue = ORDER_QUEUES[zone]
    
    # Condición de tiempo
    time_condition = False
    if queue:
        first_order_wait_time = time.time() - queue[0].timestamp
        if first_order_wait_time > MAX_TIEMPO_ESPERA:
            time_condition = True
            
    # Condición de tamaño (7 pedidos)
    size_condition = len(queue) >= MAX_PEDIDOS_TANDA
    
    if size_condition or time_condition:
        print(f"Tanda creada en zona {zone}. Tamaño: {len(queue)}. Condición de tiempo: {time_condition}")
        
        tanda_orders = create_tanda_from_queue(queue)
        
        # 5. Asignar la Tanda
        assign_tanda_to_delivery(tanda_orders)

def assign_tanda_to_delivery(tanda_orders):
    """Asigna los pedidos (ya desencolados) a un delivery disponible o a la cola de espera."""
    
    delivery = get_available_delivery()
    
    if delivery:
        # 5.1 Construir el Árbol Binario de Búsqueda (ABB)
        delivery_tree = build_delivery_route_tree(tanda_orders)
        
        # 5.2 Asignar y actualizar estado
        delivery.current_route_tree = delivery_tree
        update_delivery_state(delivery, "busy") # Cambiar estado a ocupado
        
        # 5.3 Notificar al delivery (inorden)
        notify_delivery_next_stop(delivery)
        
    else:
        # No hay disponibles, se va a la Cola de tandas
        TANDA_WAITING_QUEUE.append(tanda_orders)
        
        # Asignación aleatoria (con entrega ocupada) - REQUISITO ESPECIAL
        if TANDA_WAITING_QUEUE:
            delivery_to_assign = random.choice(get_all_deliveries()) # Seleccionar uno al azar
            # Lógica pendiente: decidir cómo manejar la sobrecarga de un delivery
            print(f"Tanda enviada a la cola de espera y asignada aleatoriamente a {delivery_to_assign.id} (ocupado).")
            # En el prototipo se podría simplificar a: TANDA_WAITING_QUEUE.append(tanda_orders)
            pass

# ====================================================================
# 5. Lógica de la Ruta (Árbol Binario de Búsqueda - ABB)
# ====================================================================

def build_delivery_route_tree(orders):
    """
    Construye el ABB basado en la distancia al restaurante.
    El nodo raíz debe ser el pedido con distancia mediana.
    """
    if not orders:
        return None
    
    # 1. Ordenar por distancia para encontrar la mediana
    orders.sort(key=lambda o: o.distance)
    
    # 2. Encontrar el índice de la mediana (aproximada, para balancear)
    mid_index = len(orders) // 2 
    
    # 3. Crear el árbol (usando una estrategia similar a la construcción de un ABB balanceado)
    abb = BinarySearchTree()
    
    # 3a. Insertar el nodo mediano (Raíz)
    median_order = orders[mid_index]
    abb.insert(median_order.distance, median_order) 
    
    # 3b. Insertar los demás pedidos
    for i, order in enumerate(orders):
        if i != mid_index:
            abb.insert(order.distance, order)
            
    # 
    return abb

def notify_delivery_next_stop(delivery):
    """
    Recorre el ABB Inorden (más cercano -> más lejano) para obtener la primera parada 
    y notificar al delivery.
    """
    if not delivery.current_route_tree:
        return None
    
    # Realizar el recorrido Inorden. El primer nodo es el más cercano.
    # Asume que el ABB tiene un método para obtener el siguiente nodo Inorden.
    next_order_node = delivery.current_route_tree.get_inorder_next() 
    
    if next_order_node:
        next_order = next_order_node.value
        # ⚠️ Aquí iría la llamada a send_message_whatsapp para notificar al Delivery
        print(f"Delivery {delivery.id}: Siguiente parada: Pedido {next_order.order_id} en {next_order.client_location}")
        return next_order
    else:
        # La ruta ha terminado.
        finish_delivery_tanda(delivery)
        return None

def process_delivery_confirmation(delivery, verification_code):
    """
    Verifica el código de un pedido y lo elimina de la ruta del ABB.
    """
    # 1. Encontrar el pedido actual (se asume que el delivery sabe cuál está entregando)
    #    Para simplificar, asumiremos que se busca en el ABB.
    
    # 2. Verificar código
    # (Lógica: buscar el pedido en el ABB, si code coincide, continuar)
    
    # 3. Eliminar el nodo actual de la ruta del ABB
    # Asume que la clave de eliminación es la distancia del pedido entregado.
    
    current_order_distance = delivery.current_route_tree.get_current_target_distance() # Obtener distancia del target
    delivery.current_route_tree.delete(current_order_distance) # Eliminación del nodo
    
    # 4. Actualizar métricas
    # (Calcular distancia y combustible gastado desde la parada anterior y sumar a delivery.metrics)
    
    # 5. Notificar la siguiente parada (si existe) o finalizar
    next_stop = notify_delivery_next_stop(delivery)
    
    # 6. Enviar mensaje de calificación al Cliente
    # (Lógica de calificación pendiente)
    
    return next_stop is not None

def finish_delivery_tanda(delivery):
    """Cuando el delivery termina la tanda, actualiza su estado y verifica la cola de espera."""
    
    print(f"Delivery {delivery.id} ha terminado la tanda.")
    
    # 1. Mostrar métricas en consola
    # (Lógica pendiente: Total de pedidos repartidos, distancia, combustible gastado)
    
    # 2. Limpiar la ruta y volver a "available"
    delivery.current_route_tree = None
    update_delivery_state(delivery, "available")
    
    # 3. Verificar si hay tandas en la cola de espera y auto-asignar (si aplica)
    if TANDA_WAITING_QUEUE:
        next_tanda = TANDA_WAITING_QUEUE.popleft()
        assign_tanda_to_delivery(next_tanda)