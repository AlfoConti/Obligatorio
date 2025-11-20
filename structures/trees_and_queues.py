# structures/trees_and_queues.py
import time
from typing import Any, List, Optional, Callable


class BSTNode:
    def __init__(self, key: float, value: Any):
        self.key = key  # por ejemplo: distancia
        self.value = value  # pedido (order dict)
        self.left: Optional['BSTNode'] = None
        self.right: Optional['BSTNode'] = None

    def insert(self, node: 'BSTNode'):
        if node.key < self.key:
            if self.left is None:
                self.left = node
            else:
                self.left.insert(node)
        else:
            if self.right is None:
                self.right = node
            else:
                self.right.insert(node)


class BSTree:
    def __init__(self):
        self.root: Optional[BSTNode] = None

    def build_from_orders(self, orders: List[dict], key_fn: Callable[[dict], float]):
        """
        Construye un BST balanceado según el enunciado: raíz = pedido mediano por distancia.
        Strategy: ordeno por key_fn, tomo mediana como root recursivamente (divide & conquer).
        """
        def build(sorted_items: List[dict]) -> Optional[BSTNode]:
            if not sorted_items:
                return None
            mid = len(sorted_items) // 2
            node = BSTNode(key=key_fn(sorted_items[mid]), value=sorted_items[mid])
            node.left = build(sorted_items[:mid])
            node.right = build(sorted_items[mid+1:])
            return node

        sorted_orders = sorted(orders, key=key_fn)
        self.root = build(sorted_orders)

    def inorder(self):
        """Devuelve lista inorder (de más cercano a más lejano si key=distancia)."""
        res = []
        def _in(node: Optional[BSTNode]):
            if not node:
                return
            _in(node.left)
            res.append(node.value)
            _in(node.right)
        _in(self.root)
        return res


class ZoneQueue:
    """
    Cola FIFO por zona. Mantiene timestamps para el primer pedido (para el criterio 45 minutos).
    """
    def __init__(self, name: str):
        self.name = name
        self._queue: List[dict] = []

    def enqueue(self, order: dict):
        order["_enqueued_at"] = time.time()
        self._queue.append(order)

    def peek(self) -> Optional[dict]:
        return self._queue[0] if self._queue else None

    def dequeue_batch(self, n: int) -> List[dict]:
        """Saca hasta n pedidos y los devuelve."""
        batch = self._queue[:n]
        self._queue = self._queue[n:]
        return batch

    def size(self) -> int:
        return len(self._queue)

    def all(self) -> List[dict]:
        return list(self._queue)
