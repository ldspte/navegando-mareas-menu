# -*- coding: utf-8 -*-
"""Dominio del menú del restaurante.
Patrones estructurales/de comportamiento: COMPOSITE (árbol carta→categoría→producto),
ITERATOR (recorrido sin exponer la estructura) y OBSERVER (ticket y migas reaccionan)."""
from abc import ABC, abstractmethod

# ============ COMPOSITE ============
class ComponenteMenu(ABC):
    def __init__(self, nombre): self.nombre = nombre
    @abstractmethod
    def contar_productos(self): ...

class Producto(ComponenteMenu):
    """Hoja del Composite."""
    def __init__(self, nombre, precio, etiquetas=None):
        super().__init__(nombre); self.precio = precio; self.etiquetas = set(etiquetas or [])
    def contar_productos(self): return 1

class Categoria(ComponenteMenu):
    """Compuesto: contiene productos y/o subcategorías, y se trata igual que una hoja."""
    def __init__(self, nombre):
        super().__init__(nombre); self.hijos = []
    def agregar(self, componente):
        self.hijos.append(componente); return self
    def contar_productos(self):
        return sum(h.contar_productos() for h in self.hijos)
    def subcategorias(self): return [h for h in self.hijos if isinstance(h, Categoria)]
    def productos(self):      return [h for h in self.hijos if isinstance(h, Producto)]

# ============ ITERATOR ============
class IteradorMenu:
    """Recorre el árbol en profundidad (DFS) devolviendo productos, sin que el
    cliente conozca la estructura interna. Cuenta los nodos visitados."""
    def __init__(self, raiz):
        self._pila = [raiz]; self.nodos_visitados = 0
    def __iter__(self): return self
    def __next__(self):
        while self._pila:
            nodo = self._pila.pop(); self.nodos_visitados += 1
            if isinstance(nodo, Categoria):
                self._pila.extend(reversed(nodo.hijos))
            else:
                return nodo
        raise StopIteration

def aplanar(carta):
    """Lista de todos los productos usando el Iterator."""
    return list(IteradorMenu(carta))

# ============ OBSERVER ============
class Observador(ABC):
    @abstractmethod
    def actualizar(self, evento, dato): ...

class Ticket(Observador):
    """Se actualiza solo cuando se selecciona un producto."""
    def __init__(self): self.items = []
    def actualizar(self, evento, dato):
        if evento == 'seleccion': self.items.append(dato)
    def total(self): return sum(p.precio for p in self.items)

class Migas(Observador):
    """Breadcrumb: muestra la ruta de navegación (Carta › Categoría › Producto)."""
    def __init__(self): self.ruta = []
    def actualizar(self, evento, dato):
        if evento == 'navegacion': self.ruta = dato

class CartaPOS:
    """Sujeto observable: la carta del POS. Notifica navegación y selección."""
    def __init__(self, raiz):
        self.raiz = raiz; self._obs = []
    def suscribir(self, o): self._obs.append(o); return self
    def notificar(self, evento, dato):
        for o in self._obs: o.actualizar(evento, dato)

# ============ BUILDER: menú real + expansión sintética ============
MENU_REAL = {
    'Desayunos':        [('Calentado con carne', 15500), ('Calentado paisa', 11000), ('Huevos al gusto', 9000)],
    'Entradas':         [('Ensalada de la casa', 14000)],
    'Platos fuertes':   [('Pollo a la plancha', 24000)],
    'Sopas':            [('Sopa del día', 12000)],
    'Bebidas calientes':[('Café americano', 4500), ('Café con leche', 5500), ('Capuchino', 6500), ('Chocolate caliente', 6000)],
    'Jugos naturales':  [('Jugo de mora', 6500), ('Jugo de naranja', 6500)],
    'Bebidas frías':    [('Café helado', 7000)],
    'Panadería':        [('Croissant', 4000), ('Pan de ayer (x3)', 4500), ('Pan de queso', 3500)],
    'Postres':          [('Brownie', 5000)],
}

def construir_carta(extra_por_categoria=0):
    """Construye la carta como Composite. `extra_por_categoria` agrega productos
    sintéticos para estudiar la escalabilidad al crecer el catálogo."""
    raiz = Categoria('Carta')
    for cat_nombre, prods in MENU_REAL.items():
        cat = Categoria(cat_nombre)
        for nombre, precio in prods:
            cat.agregar(Producto(nombre, precio, etiquetas=[cat_nombre.lower()]))
        for i in range(extra_por_categoria):
            cat.agregar(Producto(f'{cat_nombre} especial {i+1}', 5000 + i*100, etiquetas=[cat_nombre.lower()]))
        raiz.agregar(cat)
    return raiz
