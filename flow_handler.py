# flow_handler.py

from structures.data_models import get_client_by_number, get_or_create_client
from algorithms.catalog_logic import get_paginated_view, get_categories, update_client_state_for_navigation, ALL_PRODUCTS
from utils.cart_management import add_product_to_cart, generate_cart_message, get_cart_list_for_removal, remove_product_from_cart, calculate_cart_summary
from utils.geo_calculator import estimate_delivery_time, calculate_distance, RESTAURANT_LAT, RESTAURANT_LON
from algorithms.delivery_manager import place_new_order

# ====================================================================
# Definición de Estados del Grafo (Mantener en inglés por convención de código)
# ====================================================================

STATE_START = 'start'
STATE_SELECTING_PRODUCT = 'selecting_product'
STATE_SOLICITING_QUANTITY = 'soliciting_quantity'
STATE_SOLICITING_DETAILS = 'soliciting_details'
STATE_MANAGING_CART = 'managing_cart'
STATE_SOLICITING_REMOVAL = 'soliciting_removal'
STATE_SOLICITING_LOCATION = 'soliciting_location'
STATE_ORDER_PLACED = 'order_placed'
STATE_BREAK = 'break'

# Variable temporal para guardar el ID del producto que se está procesando
TEMP_PROCESSING_PRODUCT_ID = {} 

# ====================================================================
# Lógica Principal del Flujo (Central del Grafo)
# ====================================================================

def process_client_request(client, type_message, content, message_data):
    """
    Función principal que maneja el estado del cliente y determina la respuesta.
    
    :param client: Objeto Client con estado.
    :param type_message: Tipo de mensaje (text, audio, location).
    :param content: Contenido extraído del mensaje (ej: texto si es text/audio).
    :param message_data: JSON completo del mensaje (útil para la ubicación/botones).
    :return: El mensaje de texto que debe ser enviado de vuelta al usuario.
    """
    response_message = ""
    
    # 1. Manejar comandos globales y "break"
    if content and content.lower() in ["salir", "cancelar", "break"]:
        client.state = STATE_BREAK
        client.cart = {}
        return "👋 ¡Operación cancelada! Puedes volver a empezar escribiendo 'Menú' o 'Hola'."
    
    if client.state == STATE_BREAK and content and content.lower() in ["hola", "menú", "pedir"]:
        client.state = STATE_START
    
    # --- Ejecución del Grafo basada en el estado actual ---

    # ----------------------------------------------------
    # ESTADO INICIAL / VOLVER AL MENÚ
    # ----------------------------------------------------
    if client.state == STATE_START:
        client.state = STATE_SELECTING_PRODUCT
        
        # Obtener la vista inicial
        products_to_show, navigation_options, _ = get_paginated_view(client.catalog_state)
        
        # Construir el mensaje de bienvenida y listado
        response_message = f"👋 ¡Hola {client.name}! ¿Qué deseas pedir hoy?\n"
        response_message += "\n--- MENÚ DE PRODUCTOS (Pág. 1) ---\n"
        for p in products_to_show:
            response_message += f"[{p['id']}] {p['nombre']} - ${p['precio']:.2f}\n"

        response_message += "\n--- Opciones ---\n"
        response_message += "\n".join(navigation_options)
        response_message += "\n\nIndica el *ID* del producto, o elige una opción."
        
        return response_message

    # ----------------------------------------------------
    # ESTADO: SELECCIÓN DE PRODUCTO (Paginación/Filtro)
    # ----------------------------------------------------
    elif client.state == STATE_SELECTING_PRODUCT:
        
        # Si el cliente dice 'hola' en este estado, volvemos a mostrar el menú.
        if content and content.lower() in ["hola", "menú"]:
             client.catalog_state['page'] = 1 # Resetear a página 1
             return process_client_request(client, "text", "menu", message_data) 
        
        # a) El usuario seleccionó una opción de navegación (Punto d)
        if content and content.lower().startswith(("siguientes", "volver", "ordenar", "filtrar")):
            
            if content.lower() == "filtrar":
                # Lógica para mostrar la lista de categorías (Punto d.ii)
                categories = get_categories(ALL_PRODUCTS)
                client.state = 'soliciting_filter_choice' 
                return "➡️ *FILTRAR POR CATEGORÍA*\nElige una de las siguientes:\n" + ", ".join(categories)

            # Lógica para Siguientes, Volver, Ordenar
            client.catalog_state = update_client_state_for_navigation(client.catalog_state, content)
            products_to_show, navigation_options, total_pages = get_paginated_view(client.catalog_state)
            
            response = f"📋 *MENÚ* (Pág. {client.catalog_state['page']} de {total_pages})\n"
            for p in products_to_show:
                response += f"[{p['id']}] {p['nombre']} - ${p['precio']:.2f}\n"

            response += "\n--- Opciones ---\n"
            response += "\n".join(navigation_options)
            return response
            
        # b) El usuario seleccionó un producto por ID (Punto e)
        elif content and content.isdigit():
            product_id = int(content)
            product_info = next((p for p in ALL_PRODUCTS if p['id'] == product_id), None)
            
            if product_info:
                # Almacenar temporalmente el ID y cambiar de estado
                TEMP_PROCESSING_PRODUCT_ID[client.number] = product_id 
                client.state = STATE_SOLICITING_QUANTITY
                return f"Has seleccionado *{product_info['nombre']}*.\n¿Qué *cantidad* deseas agregar a tu carrito? (Ingresa solo el número)"
            else:
                return "ID de producto no válido. Intenta con un ID de la lista."
                
        # c) Mensaje inesperado
        return "Por favor, ingresa el ID de un producto, o elige una opción de navegación (ej: Siguientes productos)."
        
    # ----------------------------------------------------
    # (Resto de la lógica del grafo para otros estados: SOLICITING_QUANTITY, MANAGING_CART, etc.)
    # ----------------------------------------------------
    
    # Manejo de mensajes inesperados
    return "Disculpa, no entendí tu mensaje. ¿Deseas ver el menú principal? Escribe 'Menú'."