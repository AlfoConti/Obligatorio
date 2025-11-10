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

# ⚠️ CONFIGURACIÓN CLAVE PARA EL CATÁLOGO NATIVO DE WHATSAPP
# DEBES REEMPLAZAR ESTE ID con el ID de tu catálogo subido a Meta
WHATSAPP_CATALOG_ID = "TU_ID_DE_CATALOGO_DE_META"

# ====================================================================
# 💡 GENERACIÓN DE MENSAJES INTERACTIVOS (NUEVAS FUNCIONES)
# ====================================================================

def generate_multi_product_catalog_message(client):
    """
    Genera el payload del Mensaje de Productos Múltiples que se parece 
    a la imagen que enviaste, utilizando el catálogo previamente subido a Meta.
    """
    
    # ⚠️ NOTA: Este mensaje solo funciona si el 'catalog_id' y el 'product_retailer_id'
    # del producto están correctamente configurados en Meta.
    
    # Por el requisito de paginación (5 productos), este mensaje se complica,
    # ya que el API de Mensajes de Productos Múltiples NO soporta paginación
    # y solo envía UNA sección de hasta 30 productos.
    
    # Dado que el requisito es PAGINAR 5 productos, volvemos a la Lógica de Listas Interactiva,
    # pero la adaptamos para que se sienta más como el catálogo.
    
    # Para cumplir con la PAGINACIÓN (5 productos), USAMOS LISTAS INTERACTIVAS (Opción 1).
    # Si quieres el Catálogo NATIVO de la imagen, la paginación de 5 productos es inviable.
    
    # Volvemos al Catálogo de LISTA INTERACTIVA (con el botón + implícito)

    # Restricción: solo 5 productos por página
    client.catalog_state['page_size'] = 5 
    
    products_to_show, navigation_options, total_pages = get_paginated_view(client.catalog_state)

    sections = []

    # 1. Sección de Productos
    product_rows = []
    for p in products_to_show:
        product_rows.append({
            "id": f"product_id_{p['id']}", 
            "title": f"[{p['id']}] {p['nombre']}",
            "description": f"${p['precio']:.2f} ({p['categoria']})"
        })
    sections.append({
        "title": f"Menú - Pág. {client.catalog_state['page']} de {total_pages}",
        "rows": product_rows
    })

    # 2. Sección de Opciones
    option_rows = []
    for option in navigation_options:
        # Añade la navegación
        if option.startswith(("Siguientes", "Volver", "Ordenar", "Filtrar")):
             option_rows.append({"id": option.lower().replace(" ", "_"), "title": option, "description": "Navegar el menú"})
    
    # Opción de Carrito 
    if client.cart:
         option_rows.append({"id": "ver_carrito", "title": "🛒 Ver Carrito", "description": "Ver resumen y finalizar pedido"})


    if option_rows:
        sections.append({
            "title": "Opciones de Navegación y Compra",
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
                "text": (
                    "¡Bienvenido a BK-BOT! Selecciona un artículo de la lista para ver los detalles y agregarlo al carrito. "
                    "Solo se muestran 5 productos por página para facilitar la lectura."
                )
            },
            "action": {
                "button": "Ver Catálogo",
                "sections": sections
            }
        }
    }
    return payload


def generate_interactive_product_selection(product_info):
    """
    Genera el payload de Botones para un producto individual. 
    Aquí es donde el usuario verá el botón de '➕ Agregar al Carrito'.
    """
    
    return {
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": (
                    f"Has seleccionado: *{product_info['nombre']}*\n"
                    f"Precio: ${product_info['precio']:.2f}\n"
                    f"Descripción: {product_info['descripcion'][:100]}..." # Cortamos la descripción
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
                            "title": "Volver al Catálogo"
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
        return "👋 ¡Operación cancelada! Puedes volver a empezar escribiendo 'Catálogo' o 'Hola'."
    
    if client.state == STATE_BREAK and content and content.lower() in ["hola", "menú", "pedir", "catálogo"]:
        client.state = STATE_START
    
    # --- Ejecución del Grafo basada en el estado actual ---

    # ----------------------------------------------------
    # ESTADO INICIAL / VOLVER AL MENÚ
    # ----------------------------------------------------
    if client.state == STATE_START or (content and content.lower() in ["hola", "menú", "catálogo"]):
        client.state = STATE_SELECTING_PRODUCT
        client.catalog_state['page'] = 1 # Resetear a la página 1
        
        # 💡 Enviamos la LISTA INTERACTIVA que imita la navegación
        return generate_multi_product_catalog_message(client)

    # ----------------------------------------------------
    # ESTADO: SELECCIÓN DE PRODUCTO (Lista Interactiva)
    # ----------------------------------------------------
    elif client.state == STATE_SELECTING_PRODUCT:
        
        # a) El usuario seleccionó un PRODUCTO de la lista (ID con prefijo)
        if content and content.startswith("product_id_"):
            product_id = int(content.split('_')[-1])
            product_info = next((p for p in ALL_PRODUCTS if p['id'] == product_id), None)
            
            if product_info:
                # 💡 Enviamos el mensaje de BOTONES para agregar al carrito (similar al +)
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
            return generate_multi_product_catalog_message(client)

        # c) El usuario seleccionó VER CARRITO
        elif content == "ver_carrito":
             client.state = STATE_MANAGING_CART
             cart_message, _ = generate_cart_message(client)
             return cart_message
        
        # d) Si el usuario escribe texto plano en este estado
        return "Por favor, utiliza la opción *'Ver Catálogo'* para navegar o el comando 'Catálogo' si perdiste el botón."


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
            return f"Has seleccionado *{product_info['nombre']}*.\n¿Qué *cantidad* deseas agregar a tu carrito? (Ingresa solo el número)"
            
        else:
            client.state = STATE_SELECTING_PRODUCT
            return "Error al agregar producto. Vuelve a seleccionar en el menú principal."
            
    # El usuario presiona el botón "Volver al Menú"
    elif content == "cancel_selection":
        client.state = STATE_SELECTING_PRODUCT
        return generate_multi_product_catalog_message(client) # Mostrar el menú nuevamente


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
    # ESTADO: SOLICITANDO DETALLES (Agrega al carrito y pasa a MANAGE_CART)
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
        
        return msg + "\n\n" + cart_message


    # ----------------------------------------------------
    # ESTADO: GESTIÓN DE CARRITO
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
            return generate_multi_product_catalog_message(client) # Vuelve al catálogo
            
        elif content == "3": 
            if not client.cart:
                client.state = STATE_SELECTING_PRODUCT
                return "Tu carrito está vacío. Volviendo al menú para que puedas pedir."

            client.state = STATE_SOLICITING_LOCATION
            return "✅ *Orden a punto de confirmarse!*\nPor favor, *envíame tu ubicación* para calcular la distancia y el tiempo de entrega."
        
        # Mensaje inesperado
        cart_message, _ = generate_cart_message(client)
        return "Opción no válida. Por favor, selecciona 1, 2 o 3.\n\n" + cart_message 
    
    # ... (Resto de estados: SOLICITING_REMOVAL, SOLICITING_LOCATION, ORDER_PLACED)
    
    # Manejo de mensajes inesperados
    return "Disculpa, no entendí tu mensaje. ¿Deseas ver el menú principal? Escribe 'Catálogo'."