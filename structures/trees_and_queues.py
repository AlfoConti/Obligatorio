# structures/trees_and_queues.py

class Node:
    """
    Nodo simple para el árbol binario.
    Almacena una key y un value (ej. product_id, product_object).
    """
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.left = None
        self.right = None


# --------------------------------------------------------
# ✔ Árbol Binario de Búsqueda (BST)
# --------------------------------------------------------
class BinarySearchTree:
    """
    Árbol para búsquedas rápidas (por key).
    Puede usarse para indexar productos, categorías, etc.
    """
    def __init__(self):
        self.root = None

    # ---------------------------------------------
    def insert(self, key, value):
        """Inserta un nodo en el árbol."""
        if self.root is None:
            self.root = Node(key, value)
        else:
            self._insert_recursive(self.root, key, value)

    def _insert_recursive(self, current, key, value):
        if key < current.key:
            if current.left is None:
                current.left = Node(key, value)
            else:
                self._insert_recursive(current.left, key, value)
        else:
            if current.right is None:
                current.right = Node(key, value)
            else:
                self._insert_recursive(current.right, key, value)

    # ---------------------------------------------
    def search(self, key):
        """Busca una key en el árbol y retorna su value."""
        return self._search_recursive(self.root, key)

    def _search_recursive(self, current, key):
        if current is None:
            return None
        if key == current.key:
            return current.value
        if key < current.key:
            return self._search_recursive(current.left, key)
        return self._search_recursive(current.right, key)

    # ---------------------------------------------
    def inorder(self):
        """Retorna los elementos ordenados por key."""
        result = []
        self._inorder_recursive(self.root, result)
        return result

    def _inorder_recursive(self, current, result):
        if current:
            self._inorder_recursive(current.left, result)
            result.append((current.key, current.value))
            self._inorder_recursive(current.right, result)


# --------------------------------------------------------
# ✔ Cola (Queue) — usada para manejar pedidos o procesos
# --------------------------------------------------------
class Queue:
    """Cola FIFO simple para manejar procesos secuenciales."""
    def __init__(self):
        self.items = []

    def is_empty(self):
        return len(self.items) == 0

    def enqueue(self, item):
        """Encola un elemento al final."""
        self.items.append(item)

    def dequeue(self):
        """Desencola y retorna el primer elemento."""
        if not self.is_empty():
            return self.items.pop(0)
        return None

    def peek(self):
        """Mira el primer elemento sin quitarlo."""
        if not self.is_empty():
            return self.items[0]
        return None

    def size(self):
        return len(self.items)
