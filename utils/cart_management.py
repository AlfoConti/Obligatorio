class ShoppingCart:
    def __init__(self):
        self.items = []

    def agregar_producto(self, producto, cantidad):
        self.items.append({"producto": producto, "cantidad": cantidad})

    def quitar_producto(self, nombre):
        self.items = [i for i in self.items if i["producto"]["nombre"] != nombre]

    def total(self):
        return sum(i["producto"]["precio"] * i["cantidad"] for i in self.items)

    def mostrar_carrito(self):
        texto = "🛒 Tu carrito:\n"
        for item in self.items:
            texto += f"- {item['producto']['nombre']} x{item['cantidad']} = ${item['producto']['precio'] * item['cantidad']}\n"
        texto += f"\n💰 Total: ${self.total()}"
        return texto
