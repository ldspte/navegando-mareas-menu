# -*- coding: utf-8 -*-
"""STRATEGY: estrategias de navegación intercambiables para encontrar un producto.
Cada una devuelve (producto, pasos), donde 'pasos' = productos/etiquetas que el
usuario tuvo que revisar para llegar al objetivo (proxy del esfuerzo: toques/vistas)."""
from abc import ABC, abstractmethod
from menu import Categoria, Producto, IteradorMenu

class EstrategiaNavegacion(ABC):
    nombre = '?'
    @abstractmethod
    def buscar(self, carta, objetivo): ...

class ListaPlana(EstrategiaNavegacion):
    """Baseline: una sola lista con TODOS los productos; se escanea en orden."""
    nombre = 'Lista plana'
    def buscar(self, carta, objetivo):
        pasos = 0
        for p in IteradorMenu(carta):
            pasos += 1
            if p.nombre == objetivo:
                return p, pasos
        return None, pasos

class PorCategoria(EstrategiaNavegacion):
    """COMPOSITE: el usuario lee las categorías, entra a la correcta y escanea sus
    productos. Pasos = categorías leídas hasta la correcta + productos leídos dentro."""
    nombre = 'Por categoría'
    def buscar(self, carta, objetivo):
        pasos = 0
        for cat in carta.subcategorias():
            pasos += 1  # leer/toca el rótulo de la categoría
            prods = cat.productos()
            if any(p.nombre == objetivo for p in prods):
                for p in prods:
                    pasos += 1
                    if p.nombre == objetivo:
                        return p, pasos
        # no estaba en categorías de primer nivel: recorrido completo como respaldo
        for p in IteradorMenu(carta):
            pasos += 1
            if p.nombre == objetivo:
                return p, pasos
        return None, pasos

class Busqueda(EstrategiaNavegacion):
    """STRATEGY con índice invertido (token → productos). El índice se construye una
    vez; cada búsqueda es O(1) + los pocos candidatos que comparten el término."""
    nombre = 'Búsqueda por texto'
    def __init__(self):
        self._indice = None; self._para = None
    def _indexar(self, carta):
        idx = {}
        for p in IteradorMenu(carta):
            idx.setdefault(p.nombre.lower().strip(), []).append(p)  # índice hash por nombre
        return idx
    def buscar(self, carta, objetivo):
        if self._indice is None or self._para is not carta:
            self._indice = self._indexar(carta); self._para = carta   # una sola vez (amortizado)
        candidatos = self._indice.get(objetivo.lower().strip(), [])   # consulta directa O(1)
        pasos = 1  # la consulta al índice
        for p in candidatos:
            pasos += 1
            if p.nombre == objetivo:
                return p, pasos
        return None, pasos

class FiltroEtiqueta(EstrategiaNavegacion):
    """STRATEGY: filtra por etiqueta (p. ej. la categoría) y escanea el subconjunto."""
    nombre = 'Filtro por etiqueta'
    def buscar(self, carta, objetivo, etiqueta=None):
        pasos = 1  # aplicar el filtro
        for p in IteradorMenu(carta):
            if etiqueta and etiqueta not in p.etiquetas:
                continue
            pasos += 1
            if p.nombre == objetivo:
                return p, pasos
        return None, pasos

ESTRATEGIAS = [ListaPlana(), PorCategoria(), Busqueda()]
