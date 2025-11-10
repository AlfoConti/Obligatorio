# structures/trees_and_queues.py

from collections import deque

# La estructura global ORDER_QUEUES se define y gestiona en delivery_manager.py.
# Aquí solo definimos la estructura del Nodo para el ABB.

# ====================================================================
# 2. Árbol Binario de Búsqueda (ABB) para Rutas de Entrega
# ====================================================================

class Node:
    """Nodo básico para el Árbol Binario de Búsqueda."""
    def __init__(self, key, value):
        # La clave (key) es la distancia al restaurante.
        self.key = key 
        # El valor (value) es el objeto Order (Pedido).
        self.value = value 
        self.left = None
        self.right = None

class BinarySearchTree:
    """
    Implementación del Árbol Binario de Búsqueda para organizar los pedidos 
    de una Tanda por distancia (más cercano a más lejano).
    """
    def __init__(self):
        self.root = None
        # Atributo para seguir el recorrido Inorden actual del delivery
        self._last_inorder_key = None 
        self._current_target_distance = None # Distancia del pedido que el delivery está entregando

    def insert(self, key, value):
        """Inserta un nuevo pedido basado en su distancia (key)."""
        if self.root is None:
            self.root = Node(key, value)
        else:
            self._insert_recursive(key, value, self.root)

    def _insert_recursive(self, key, value, node):
        if key < node.key:
            if node.left is None:
                node.left = Node(key, value)
            else:
                self._insert_recursive(key, value, node.left)
        elif key > node.key:
            if node.right is None:
                node.right = Node(key, value)
            else:
                self._insert_recursive(key, value, node.right)
        # Ignoramos claves iguales (distancias iguales) para la simplificación del prototipo,
        # aunque en producción se manejarían para evitar pérdida de datos.

    def delete(self, key):
        """
        Elimina un pedido (Nodo) del árbol después de ser entregado.
        Esta operación es crítica para el requisito de la consigna.
        """
        self.root = self._delete_recursive(self.root, key)
        self._current_target_distance = None # Reiniciar después de eliminar

    def _delete_recursive(self, root, key):
        if root is None:
            return root
        
        if key < root.key:
            root.left = self._delete_recursive(root.left, key)
        elif key > root.key:
            root.right = self._delete_recursive(root.right, key)
        else:
            # Caso 1: Nodo con 0 o 1 hijo
            if root.left is None:
                return root.right
            elif root.right is None:
                return root.left
            
            # Caso 2: Nodo con 2 hijos
            # Encontramos el sucesor Inorden (el mínimo en el subárbol derecho)
            temp = self._min_value_node(root.right)
            
            # Copiamos el contenido del sucesor Inorden a este nodo
            root.key = temp.key
            root.value = temp.value
            
            # Eliminamos el sucesor Inorden
            root.right = self._delete_recursive(root.right, temp.key)
            
        return root

    def _min_value_node(self, node):
        """Encuentra el nodo con el valor clave más pequeño en un subárbol."""
        current = node
        while current.left is not None:
            current = current.left
        return current
        
    def get_inorder_next(self):
        """
        Implementa la lógica del recorrido Inorden (de menor a mayor clave/distancia)
        para obtener el siguiente pedido de la ruta del delivery.
        """
        
        # Si es la primera vez, se comienza desde el nodo con la clave más pequeña (más cercano).
        if self._last_inorder_key is None:
            if self.root is None:
                return None
            current = self._min_value_node(self.root)
            if current:
                self._last_inorder_key = current.key
                self._current_target_distance = current.key
                return current
        
        # Si no es la primera vez, se busca el sucesor Inorden.
        
        # Lógica simplificada: para el prototipo, se puede re-ejecutar una búsqueda Inorden 
        # y detenerse en el nodo inmediatamente posterior a _last_inorder_key.
        
        successor = self._find_inorder_successor(self.root, self._last_inorder_key)
        
        if successor:
            self._last_inorder_key = successor.key
            self._current_target_distance = successor.key
            return successor
        
        # Si no hay sucesor, la tanda ha terminado.
        return None
        
    def _find_inorder_successor(self, root, target_key):
        """Busca el sucesor Inorden (el siguiente nodo en orden ascendente)."""
        successor = None
        while root:
            if target_key >= root.key:
                root = root.right
            else:
                successor = root
                root = root.left
        return successor
        
    def get_current_target_distance(self):
        """Retorna la distancia del pedido que se está entregando actualmente."""
        return self._current_target_distance