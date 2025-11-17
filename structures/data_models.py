# models/data_models.py

from pydantic import BaseModel
from typing import List, Optional


# ---------------------------------------------------------
# ✔ Producto del catálogo
# ---------------------------------------------------------
class Product(BaseModel):
    id: int
    name: str
    price: float
    description: Optional[str] = None
    stock: int = 0
    image: Optional[str] = None  # URL de imagen si usas en el frontend


# ---------------------------------------------------------
# ✔ Item dentro del carrito
# ---------------------------------------------------------
class CartItem(BaseModel):
    product_id: int
    quantity: int


# ---------------------------------------------------------
# ✔ Carrito completo del usuario
# ---------------------------------------------------------
class Cart(BaseModel):
    items: List[CartItem] = []

    def total(self, products_dict):
        """
        Calcula el total utilizando un diccionario:
        {id_producto: objeto_producto}
        """
        total_amount = 0
        for item in self.items:
            if item.product_id in products_dict:
                total_amount += products_dict[item.product_id].price * item.quantity
        return total_amount


# ---------------------------------------------------------
# ✔ Información de usuario (para pedidos y WhatsApp)
# ---------------------------------------------------------
class UserInfo(BaseModel):
    name: str
    phone: str  # número formateado para WhatsApp
    address: Optional[str] = None  # solo si elige delivery
    email: Optional[str] = None


# ---------------------------------------------------------
# ✔ Tipos de entrega
# ---------------------------------------------------------
class DeliveryMethod(BaseModel):
    """
    1 → Delivery a domicilio (requiere dirección)
    2 → Retiro en local
    """
    type: int  # 1 = delivery, 2 = pickup
    address: Optional[str] = None


# ---------------------------------------------------------
# ✔ Pedido / Orden final
# ---------------------------------------------------------
class Order(BaseModel):
    id: int
    user: UserInfo
    cart: Cart
    delivery: DeliveryMethod
    total: float
    status: str = "PENDING"  # PENDING / CONFIRMED / CANCELLED

