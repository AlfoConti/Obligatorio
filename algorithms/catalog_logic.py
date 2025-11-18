# algorithms/catalog_logic.py

# Tu catálogo REAL
catalog = [
    { "id": 1, "nombre": "Hamburguesa Clásica", "categoria": "Minutas", "precio": 450.00, "descripcion": "Carne, queso cheddar, lechuga y aderezo especial." },
    { "id": 2, "nombre": "Pizza Margarita", "categoria": "Pizzas", "precio": 520.00, "descripcion": "Salsa de tomate, mozzarella y albahaca fresca." },
    { "id": 3, "nombre": "Refresco Cola (Lata)", "categoria": "Bebidas", "precio": 120.00, "descripcion": "Lata de 350ml." },
    { "id": 4, "nombre": "Papas Fritas Grandes", "categoria": "Acompañamientos", "precio": 210.00, "descripcion": "Porción grande de papas fritas rústicas." },
    { "id": 5, "nombre": "Tarta de Manzana", "categoria": "Postres", "precio": 280.00, "descripcion": "Clásica tarta con helado de vainilla." },
    { "id": 6, "nombre": "Milanesa a Caballo", "categoria": "Minutas", "precio": 610.00, "descripcion": "Milanesa de ternera con dos huevos fritos." },
    { "id": 7, "nombre": "Pizza Pepperoni", "categoria": "Pizzas", "precio": 650.00, "descripcion": "Masa fina, mozzarella y pepperoni." },
    { "id": 8, "nombre": "Agua Mineral sin Gas", "categoria": "Bebidas", "precio": 90.00, "descripcion": "Botella de 500ml." },
    { "id": 9, "nombre": "Ensalada César", "categoria": "Ensaladas", "precio": 390.00, "descripcion": "Pollo grillado, crutones, queso parmesano y aderezo César." },
    { "id": 10, "nombre": "Lomito Completo", "categoria": "Minutas", "precio": 720.00, "descripcion": "Lomo, jamón, queso, huevo, panceta, lechuga y tomate." },
    { "id": 11, "nombre": "Pizza Fugazza", "categoria": "Pizzas", "precio": 500.00, "descripcion": "Cebolla, orégano y abundante mozzarella." },
    { "id": 12, "nombre": "Jugo de Naranja Natural", "categoria": "Bebidas", "precio": 150.00, "descripcion": "Jugo de naranja exprimido al momento." },
    { "id": 13, "nombre": "Aros de Cebolla", "categoria": "Acompañamientos", "precio": 250.00, "descripcion": "Crujientes aros de cebolla con salsa BBQ." },
    { "id": 14, "nombre": "Flan Casero", "categoria": "Postres", "precio": 260.00, "descripcion": "Flan de huevo con dulce de leche y crema." },
    { "id": 15, "nombre": "Sándwich Vegetariano", "categoria": "Vegetariano", "precio": 410.00, "descripcion": "Pan integral, palta, rúcula, tomate y queso." },
    { "id": 16, "nombre": "Suprema de Pollo", "categoria": "Minutas", "precio": 580.00, "descripcion": "Pechuga de pollo empanada y frita." },
    { "id": 17, "nombre": "Pizza Napolitana", "categoria": "Pizzas", "precio": 580.00, "descripcion": "Tomate, mozzarella, ajo y perejil." },
    { "id": 18, "nombre": "Cerveza Artesanal IPA", "categoria": "Cervezas", "precio": 320.00, "descripcion": "Botella de 500ml." },
    { "id": 19, "nombre": "Bastones de Muzzarella", "categoria": "Acompañamientos", "precio": 290.00, "descripcion": "Ocho bastones de queso con salsa de tomate." },
    { "id": 20, "nombre": "Helado Artesanal", "categoria": "Postres", "precio": 310.00, "descripcion": "Dos bochas, sabores a elección." },
    { "id": 21, "nombre": "Wrap de Pollo", "categoria": "Minutas", "precio": 480.00, "descripcion": "Tortilla de trigo, pollo desmenuzado, verduras y salsa." },
    { "id": 22, "nombre": "Pizza Cuatro Quesos", "categoria": "Pizzas", "precio": 680.00, "descripcion": "Mozzarella, Roquefort, Parmesano y Fontina." },
    { "id": 23, "nombre": "Vino Tinto Malbec", "categoria": "Vinos", "precio": 950.00, "descripcion": "Botella de 750ml, reserva." },
    { "id": 24, "nombre": "Sopa del Día", "categoria": "Otros", "precio": 300.00, "descripcion": "Consultar variedad al mozo (ej: Calabaza)." },
    { "id": 25, "nombre": "Brownie con Nuez", "categoria": "Postres", "precio": 290.00, "descripcion": "Brownie tibio con nueces." }
]


def get_catalog():
    """
    Devuelve el catálogo formateado en texto para WhatsApp.
    """

    header = "📦 *Catálogo de productos*\n\n"

    lines = []

    for item in catalog:
        line = (
            f"*{item['id']}. {item['nombre']}*\n"
            f"_{item['categoria']}_ • 💵 ${item['precio']}\n"
            f"{item['descripcion']}\n\n"
        )
        lines.append(line)

    body = "".join(lines)

    footer = "➡ Para agregar al carrito escribe:\n*agregar <id>*\nEjemplo: agregar 3"

    return header + body + footer
