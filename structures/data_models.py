# structures/data_models.py
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class Product:
    id: int
    name: str
    category: str
    price: float

@dataclass
class CartItem:
    product_id: int
    qty: int
    details: str

@dataclass
class Order:
    id: int
    phone: str
    items: List[CartItem]
    total: float
    created_at: datetime
    status: str
    code: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    distance_km: Optional[float] = None
