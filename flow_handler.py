# flow_handler.py

from structures.data_models import get_client_by_number, get_or_create_client
from algorithms.catalog_logic import get_paginated_view, get_categories, update_client_state_for_navigation, ALL_PRODUCTS
from utils.cart_management import add_product_to_cart, generate_cart_message, get_cart_list_for_removal, remove_product_from_cart, calculate_cart_summary
from utils.geo_calculator import estimate_delivery_time, calculate_distance, RESTAURANT_LAT, RESTAURANT_LON
from algorithms.delivery_manager import place_new_order

# ====================================================================
# Definición de Estados del Grafo
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
# 💡 GENERACIÓN DE MENSAJES INTERACTIVOS (FUNCIONES)
# ====================================================================

def generate_interactive_catalog(client):
    """Genera el payload de la Lista Interactiva para el catálogo (Punto d)."""
    
    # Restricción: solo 5 productos por página
    client.catalog_state['page_size'] = 5 
    
    products_to_show, navigation_options, total_pages = get_paginated_view(client.catalog_state)

    # Creamos las secciones de la lista
    sections = []

    # 1. Sección de Productos
    product_rows = []
    for p in products_to_show:
        product_rows.append({
            "id": f"product_id_{p['id']}", # Usaremos este ID para el manejo del estado
            "title": f"[{p['id']}] {p['nombre']}",
            "description": f"${p['precio']:.2f} ({p['categoria']})"
        })
    sections.append({
        "title": f"Menú - Pág. {client.catalog_state['page']} de {total_pages}",
        "rows": product_rows
    })

    # 2. Sección de Opciones
    option_rows = []
    # Usamos los nombres de navegación existentes como IDs/Títulos
    for option in navigation_options:
        if option.startswith(("Siguientes", "Volver")):
             option_rows.append({"id": option.lower().replace(" ", "_"), "title": option, "description": "Navegar el menú"})
        elif option == "Ordenar":
             option_rows.append({"id": "ordenar", "title": option, "description": "Cambiar el orden de visualización"})
        elif option == "Filtrar":
             option_rows.append({"id": "filtrar", "title": option, "description": "Buscar por categoría"})
    
    # Opción de Carrito (si no está vacío)
    if client.cart:
         option_rows.append({"id": "ver_carrito", "title": "🛒 Ver Carrito", "description": "Ver resumen y finalizar pedido"})


    if option_rows:
        sections.append({
            "title": "Opciones de Navegación",
            "rows": option_rows
        })
    
    # Payload final para el mensaje interactivo (Lista)
    payload = {
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {
                "type": "text",
                "text": "Selecciona una opción o un producto del menú."
            },
            "body": {
                "text": f"¡Hola {client.name}! Revisa nuestro menú. Solo se muestran 5 productos por página."
            },
            "action": {
                "button": "Ver Menú",
                "sections": sections
            }
        }
    }
    return payload


def generate_interactive_product_selection(product_info):
    """Genera el payload de Botones para un producto individual (Botón '+ Agregar')."""
    
    return {
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": (
                    f"Has seleccionado: *{product_info['nombre']}*\n"
                    f"Precio: ${product_info['precio']:.2f}\n"
                    f"Descripción: {product_info['descripcion'][:50]}..."
                )
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            # El ID lleva la acción y el ID del producto
                            "id": f"add_product_{product_info['id']}", 
                            "title": "➕ Agregar al Carrito"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "cancel_selection",
                            "title": "Volver al Menú"
                        }
                    }
                ]
            }
        }
    }


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
    :return: El mensaje de texto (str) o el payload interactivo (dict) a enviar.
    """
    
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
    if client.state == STATE_START or (content and content.lower() in ["hola", "menú", "catálogo"]):
        client.state = STATE_SELECTING_PRODUCT
        client.catalog_state['page'] = 1 # Resetear a la página 1
        
        # 💡 Enviamos la LISTA INTERACTIVA (el catálogo paginado)
        return generate_interactive_catalog(client)

    # ----------------------------------------------------
    # ESTADO: SELECCIÓN DE PRODUCTO (Lista Interactiva)
    # ----------------------------------------------------
    elif client.state == STATE_SELECTING_PRODUCT:
        
        # a) El usuario seleccionó un PRODUCTO de la lista (ID con prefijo)
        if content and content.startswith("product_id_"):
            product_id = int(content.split('_')[-1])
            product_info = next((p for p in ALL_PRODUCTS if p['id'] == product_id), None)
            
            if product_info:
                # 💡 Enviamos el mensaje de BOTONES para agregar al carrito (simulando el '+')
                return generate_interactive_product_selection(product_info)
            else:
                return "Producto no encontrado. Selecciona uno válido del menú."
        
        # b) El usuario seleccionó una OPCIÓN de navegación (ID sin prefijo)
        elif content in ["siguientes_productos", "volver_pagina", "ordenar", "filtrar"]:
            
            if content == "filtrar":
                # Lógica para mostrar la lista de categorías 
                categories = get_categories(ALL_PRODUCTS)
                client.state = 'soliciting_filter_choice' 
                return "➡️ *FILTRAR POR CATEGORÍA*\nElige una de las siguientes:\n" + ", ".join(categories)

            # Lógica para Siguientes, Volver, Ordenar
            content_text = content.replace("_", " ") # Convertir a formato legible
            client.catalog_state = update_client_state_for_navigation(client.catalog_state, content_text)
            
            # Volvemos a mostrar el catálogo actualizado
            return generate_interactive_catalog(client)

        # c) El usuario seleccionó VER CARRITO
        elif content == "ver_carrito":
             client.state = STATE_MANAGING_CART
             cart_message, _ = generate_cart_message(client)
             return cart_message
        
        # d) Si el usuario escribe texto plano en este estado
        return "Por favor, utiliza la opción *'Ver Menú'* para navegar o el comando 'Menú' si perdiste el botón."


    # ----------------------------------------------------
    # ESTADO: BOTONES DE SELECCIÓN DE PRODUCTO (add_product, cancel_selection)
    # ----------------------------------------------------
    # El usuario presiona el botón "Agregar al Carrito"
    elif content and content.startswith("add_product_"):
        
        product_id = int(content.split('_')[-1])
        product_info = next((p for p in ALL_PRODUCTS if p['id'] == product_id), None)
        
        if product_info:
            # Almacenar temporalmente el ID y pasar a pedir cantidad
            TEMP_PROCESSING_PRODUCT_ID[client.number] = product_id 
            client.state = STATE_SOLICITING_QUANTITY
            return f"Has seleccionado *{product_info['nombre']}*.\n¿Qué *cantidad* deseas agregar? (Ingresa solo el número)"
            
        else:
            client.state = STATE_SELECTING_PRODUCT
            return "Error al agregar producto. Vuelve a seleccionar en el menú principal."
            
    # El usuario presiona el botón "Volver al Menú"
    elif content == "cancel_selection":
        client.state = STATE_SELECTING_PRODUCT
        return generate_interactive_catalog(client) # Mostrar el menú nuevamente


    # ----------------------------------------------------
    # ESTADO: SOLICITANDO CANTIDAD 
    # ----------------------------------------------------
    elif client.state == STATE_SOLICITING_QUANTITY:
        
        if content and content.isdigit():
            quantity = int(content)
            product_id = TEMP_PROCESSING_PRODUCT_ID.get(client.number)
            
            if product_id is None or quantity <= 0:
                 client.state = STATE_SELECTING_PRODUCT
                 return "Cantidad no válida o error de proceso. Volviendo al menú."
                 
            # Guardamos la cantidad en el temporal para usarla con los detalles
            TEMP_PROCESSING_PRODUCT_ID[client.number] = {'id': product_id, 'quantity': quantity}
            client.state = STATE_SOLICITING_DETAILS
            
            return f"Perfecto, *{quantity} unidad(es)*. Ahora, ¿tienes algún detalle o especificación? (ej: 'sin tomate').\nSi no tienes detalles, simplemente escribe 'No'."
        
        return "Por favor, ingresa una cantidad válida (solo números)."


    # ----------------------------------------------------
    # ESTADO: SOLICITANDO DETALLES 
    # ----------------------------------------------------
    elif client.state == STATE_SOLICITING_DETAILS:
        
        temp_data = TEMP_PROCESSING_PRODUCT_ID.get(client.number)
        
        if not temp_data or 'id' not in temp_data:
            client.state = STATE_SELECTING_PRODUCT
            return "Error de proceso. Volviendo al menú."

        product_id = temp_data['id']
        quantity = temp_data.get('quantity', 1) 
        details = content if content.lower() != 'no' else ""

        # AGREGAR AL CARRITO
        success, msg = add_product_to_cart(client, product_id, quantity=quantity, details=details) 
        
        # Volver al manejo del carrito
        client.state = STATE_MANAGING_CART
        
        # Generar mensaje del carrito y opciones 
        cart_message, _ = generate_cart_message(client) 
        
        return cart_message


    # ----------------------------------------------------
    # ESTADO: GESTIÓN DE CARRITO (Texto plano con opciones)
    # ----------------------------------------------------
    elif client.state == STATE_MANAGING_CART:
        # 1: Quitar, 2: Seguir Pidiendo, 3: Confirmar Orden
        
        if content == "1": 
            client.state = STATE_SOLICITING_REMOVAL
            removal_message, _, _ = get_cart_list_for_removal(client)
            return removal_message
            
        elif content == "2": 
            client.state = STATE_SELECTING_PRODUCT
            client.catalog_state['page'] = 1 
            return generate_interactive_catalog(client) # Vuelve al catálogo interactivo
            
        elif content == "3": 
            if not client.cart:
                client.state = STATE_SELECTING_PRODUCT
                return "Tu carrito está vacío. Volviendo al menú para que puedas pedir."

            client.state = STATE_SOLICITING_LOCATION
            return "✅ *Orden a punto de confirmarse!*\nPor favor, *envíame tu ubicación* para calcular la distancia y el tiempo de entrega."
        
        # Mensaje inesperado
        cart_message, _ = generate_cart_message(client)
        return "Opción no válida. Por favor, selecciona 1, 2 o 3.\n\n" + cart_message 

    # ----------------------------------------------------
    # ESTADO: SOLICITANDO UBICACIÓN 
    # ----------------------------------------------------
    elif client.state == STATE_SOLICITING_LOCATION:
        
        if type_message == "location":
            location = message_data.get('location', {})
            client_lat = location.get('latitude')
            client_lon = location.get('longitude')
            
            client_location = (client_lat, client_lon)
            restaurant_location = (RESTAURANT_LAT, RESTAURANT_LON)
            
            distance_km = calculate_distance(restaurant_location, client_location)
            time_min = estimate_delivery_time(distance_km)
            
            summary, total = calculate_cart_summary(client)
            order_data = {'products': summary, 'total': total}
            
            new_order = place_new_order(order_data, client_location)
            
            client.state = STATE_ORDER_PLACED
            
            response = (
                f"🎉 *¡Pedido Confirmado!* 🎉\n\n"
                f"Distancia al restaurante: *{distance_km:.2f} km*\n"
                f"Tiempo de entrega estimado: *{int(time_min)} minutos*\n"
                f"Tu código de verificación es: *{new_order.verification_code}*\n\n"
                f"Te notificaremos cuando tu {new_order.zone} delivery esté en camino. ¡Gracias!"
            )
            client.cart = {}
            return response
        
        return "Por favor, *envíame tu ubicación* para poder procesar la entrega."

    # ----------------------------------------------------
    # ESTADO: SOLICITANDO REMOCIÓN 
    # ----------------------------------------------------
    elif client.state == STATE_SOLICITING_REMOVAL:
        
        if content and content.isdigit():
            index_to_remove = int(content) - 1
            
            removal_message, product_id, item_index = get_cart_list_for_removal(client)
            
            if 0 <= index_to_remove < len(item_index):
                cart_key = item_index[index_to_remove]
                remove_product_from_cart(client, cart_key)
                
                # Volver a la gestión de carrito
                client.state = STATE_MANAGING_CART
                cart_message, _ = generate_cart_message(client) 
                return f"✅ Producto eliminado del carrito.\n\n{cart_message}"
            else:
                return f"Número no válido. Ingresa el número del producto que deseas eliminar (1-{len(item_index)}) o escribe 'Cancelar'."
        
        return "Por favor, ingresa el número del producto a eliminar o 'Cancelar' para volver."


    # Si el estado es inesperado o final, se vuelve a START
    client.state = STATE_START
    return "Error de estado. Escribe 'Hola' para reiniciar el menú."