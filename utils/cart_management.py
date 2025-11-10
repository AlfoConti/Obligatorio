# utils/cart_management.py

from structures.data_models import get_client_by_number
from algorithms.catalog_logic import ALL_PRODUCTS # Acceso al catálogo completo

# ====================================================================
# Funciones de Soporte
# ====================================================================

def get_product_info(product_id):
    """Busca y retorna el objeto Producto completo basado en su ID."""
    # Se busca en la lista cargada de products_dataset.json
    for product in ALL_PRODUCTS:
        if product.get('id') == product_id:
            # Crea un objeto Product para fácil acceso (Asumiendo que Product existe en data_models)
            return product 
    return None

def calculate_cart_summary(client):
    """
    Calcula el subtotal de cada ítem y el total del carrito.
    
    :param client: Objeto Client con el carrito cargado.
    :return: (listado_de_items_con_subtotal, total_carrito)
    """
    summary = []
    total = 0.0

    # client.cart tiene el formato: {product_id: {'quantity': N, 'details': 'sin tomate'}}
    for product_id, item_data in client.cart.items():
        product_info = get_product_info(product_id)
        
        if product_info:
            precio_unitario = product_info.get('precio', 0.0)
            cantidad = item_data['quantity']
            subtotal = precio_unitario * cantidad
            total += subtotal
            
            summary.append({
                "id": product_id,
                "nombre": product_info['nombre'],
                "cantidad": cantidad,
                "precio_unitario": precio_unitario,
                "subtotal": subtotal,
                "detalles": item_data['details']
            })
            
    return summary, total

# ====================================================================
# Lógica de Carrito (Punto f)
# ====================================================================

def add_product_to_cart(client, product_id, quantity, details=""):
    """
    Agrega o actualiza un producto en el carrito del cliente (estructura temporal).
    """
    product_id = int(product_id)
    
    # Validar la cantidad
    if quantity <= 0:
        return False, "La cantidad debe ser un número positivo."

    if product_id in client.cart:
        # El producto ya está, se actualiza la cantidad y los detalles
        client.cart[product_id]['quantity'] += quantity
        client.cart[product_id]['details'] = details # Sobreescribir detalles o concatenar si es más complejo
    else:
        # Producto nuevo
        client.cart[product_id] = {
            'quantity': quantity,
            'details': details
        }
        
    return True, f"{quantity}x {get_product_info(product_id)['nombre']} agregado(s) al carrito."

def remove_product_from_cart(client, product_id):
    """
    Elimina un producto del carrito.
    """
    product_id = int(product_id)
    
    if product_id in client.cart:
        product_name = get_product_info(product_id)['nombre']
        del client.cart[product_id]
        return True, f"'{product_name}' ha sido eliminado del carrito."
    
    return False, "Ese producto no se encontró en tu carrito."

# ====================================================================
# Generación de Mensaje para WhatsApp (Punto g)
# ====================================================================

def generate_cart_message(client):
    """
    Genera el mensaje de resumen del carrito con las opciones de acción.
    """
    summary, total = calculate_cart_summary(client)
    
    if not summary:
        return "Tu carrito está vacío. ¡Añade productos para continuar!", []

    # Construir el cuerpo del mensaje de resumen (Punto g)
    message_body = "🛒 *Tu Carrito de Compras:*\n"
    
    for item in summary:
        line = (
            f"  - *{item['cantidad']}x {item['nombre']}* "
            f"(${item['precio_unitario']:.2f} c/u)\n"
            f"    *Subtotal:* ${item['subtotal']:.2f}"
        )
        if item['detalles']:
            line += f" (Detalles: {item['detalles']})"
        message_body += line + "\n"
        
    message_body += f"\n💰 *Total del Pedido:* ${total:.2f}\n"

    # Opciones requeridas (Punto g.i, g.ii, g.iii)
    options = [
        "1. Quitar producto", 
        "2. Seguir pidiendo productos", 
        "3. Confirmar orden"
    ]
    
    message_body += "\n¿Qué deseas hacer ahora?\n" + "\n".join(options)
    
    return message_body, options

def get_cart_list_for_removal(client):
    """
    Genera una lista numerada del carrito para la opción 'Quitar producto'.
    """
    summary, _ = calculate_cart_summary(client)
    
    if not summary:
        return "El carrito está vacío."

    message = "🗑️ *Selecciona el número del producto a quitar:*\n"
    options = []
    
    for i, item in enumerate(summary, 1):
        message += f"{i}. {item['cantidad']}x {item['nombre']} (${item['subtotal']:.2f})\n"
        options.append(str(i)) # Opciones son los índices (1, 2, 3...)
        
    return message, options, summary