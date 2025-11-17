# structures/trees_and_queues.py

class SimpleQueue:
    """
    Cola simple FIFO usada para:
    - Colas de pedidos por zona (NE, NO, SE, SO)
    - Cola de tandas pendientes cuando no hay delivery disponible
    """

    def __init__(self):
        self.items = []

    # ──────────────────────────────────────────────
    # Insertar al final de la cola
    # ──────────────────────────────────────────────
    def enqueue(self, value):
        self.items.append(value)

    # ──────────────────────────────────────────────
    # Sacar el primer elemento
    # ──────────────────────────────────────────────
    def dequeue(self):
        if not self.is_empty():
            return self.items.pop(0)
        return None

    # ──────────────────────────────────────────────
    # Ver el primer elemento sin sacarlo
    # ──────────────────────────────────────────────
    def peek(self):
        if not self.is_empty():
            return self.items[0]
        return None

    # ──────────────────────────────────────────────
    # Tamaño actual de la cola
    # ──────────────────────────────────────────────
    def size(self):
        return len(self.items)

    # ──────────────────────────────────────────────
    # ¿Está vacía?
    # ──────────────────────────────────────────────
    def is_empty(self):
        return len(self.items) == 0

    # ──────────────────────────────────────────────
    # Obtener todos los elementos (debug / reportes)
    # ──────────────────────────────────────────────
    def list_items(self):
        return list(self.items)
