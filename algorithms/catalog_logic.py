# catalog_logic.py

import json

# ====================================================================
# 1. Carga de Datos (Simulación)
# NOTA: En un entorno real, este catálogo se cargaría desde una base de datos.
# Aquí simularemos la carga desde 'data/products_dataset.json'
# ====================================================================

def load_products_data():
    """Carga el catálogo completo de productos."""
    try:
        # Se asume que el archivo products_dataset.json está bien formateado
        with open('data/products_dataset.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: El archivo data/products_dataset.json no fue encontrado.")
        return []
    except json.JSONDecodeError:
        print("Error: El archivo data/products_dataset.json no es un JSON válido.")
        return []

# Carga la lista base de productos
ALL_PRODUCTS = load_products_data()

# ====================================================================
# 2. Lógica de Filtrado y Ordenamiento
# ====================================================================

def get_categories(products):
    """Extrae las categorías únicas de los productos."""
    categories = set(p.get('categoria', 'Otros') for p in products)
    # Asegurarse de que 'Todos' esté al principio y que no haya más de 10
    return ["Todos"] + sorted(list(categories))[:9] 

def filter_products(products, filter_key):
    """Filtra la lista de productos por categoría."""
    if filter_key is None or filter_key.lower() == "todos":
        return products
    return [p for p in products if p.get('categoria') == filter_key]

def sort_products(products, sort_order):
    """
    Ordena la lista de productos por precio.
    'asc' para ascendente (más barato a más caro).
    'desc' para descendente (más caro a más barato).
    """
    reverse_flag = (sort_order.lower() == 'desc') # True si es descendente
    
    # Se usa el sort nativo de Python que es una implementación de Timsort, muy eficiente.
    sorted_products = sorted(products, key=lambda p: p.get('precio', 0), reverse=reverse_flag)
    return sorted_products


# ====================================================================
# 3. Lógica de Paginación y Generación de la Vista
# ====================================================================

# Constante para el tamaño de la página
PAGE_SIZE = 5 

def get_paginated_view(client_state):
    """
    Aplica filtros y ordenamiento según el estado del cliente y genera 
    la lista de productos a mostrar y las opciones de navegación.
    
    :param client_state: Diccionario con 'page', 'filter', 'order'.
    :return: (listado_productos_para_mostrar, listado_de_opciones_de_navegacion)
    """
    current_page = client_state.get('page', 1)
    current_filter = client_state.get('filter', 'Todos')
    current_order = client_state.get('order', 'asc') # 'asc' o 'desc'

    # 1. Aplicar Filtrado
    filtered_products = filter_products(ALL_PRODUCTS, current_filter)
    
    # 2. Aplicar Ordenamiento
    final_list = sort_products(filtered_products, current_order)
    
    total_items = len(final_list)
    total_pages = (total_items + PAGE_SIZE - 1) // PAGE_SIZE # Cálculo de páginas al alza
    
    # 3. Paginación (Slicing de la lista)
    start_index = (current_page - 1) * PAGE_SIZE
    end_index = start_index + PAGE_SIZE
    
    products_to_show = final_list[start_index:end_index]
    
    # 4. Generar Opciones de Navegación (Punto d.i a d.vi)
    navigation_options = []
    
    # Opción 1: Filtrar (d.ii)
    navigation_options.append("Filtrar") 
    
    # Opción 2: Ordenar (d.iii)
    order_label = "Ordenar: Precio (Desc)" if current_order == 'asc' else "Ordenar: Precio (Asc)"
    navigation_options.append(order_label)
    
    # Opción 3: Siguientes productos (d.iv)
    if current_page < total_pages:
        navigation_options.append("Siguientes productos (5)")
        
    # Opción 4: Volver (d.v)
    if current_page >= 2:
        navigation_options.append("Volver (5 anteriores)")
        
    # Opción 5: Volver al Inicio (d.vi)
    if current_page >= 3:
        navigation_options.append("Volver al Inicio (Pág. 1)")
        
    return products_to_show, navigation_options, total_pages

# ====================================================================
# 4. Lógica de Navegación (Usada por flow_handler.py)
# ====================================================================

def update_client_state_for_navigation(client_state, action):
    """
    Actualiza el estado del cliente (página, filtro, orden) basado en la acción 
    seleccionada por el usuario.
    """
    current_page = client_state.get('page', 1)
    current_order = client_state.get('order', 'asc')
    
    # El filtro se actualiza en otro punto, esta función maneja solo navegación y orden.
    
    if "Siguientes" in action:
        client_state['page'] = current_page + 1
    elif "Volver (5 anteriores)" in action:
        client_state['page'] = max(1, current_page - 1)
    elif "Volver al Inicio" in action:
        client_state['page'] = 1
    elif "Ordenar" in action:
        # Alterna el orden y resetea a página 1
        client_state['order'] = 'desc' if current_order == 'asc' else 'asc'
        client_state['page'] = 1
    # Nota: La lógica de 'Filtrar' será manejada por flow_handler.py 
    # para solicitar la nueva categoría al usuario.
        
    return client_state