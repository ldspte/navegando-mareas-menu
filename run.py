# -*- coding: utf-8 -*-
"""Navegando mareas — prototipo de estrategias de navegación del menú.
Escenario A: escalabilidad (pasos y tiempo por estrategia al crecer la carta).
Escenario B: validación + Observer (navegar a un producto y actualizar ticket/migas).

Uso:  python run.py            (ambos escenarios)
      python run.py escalabilidad | validacion
Solo biblioteca estándar; matplotlib es opcional (solo para el gráfico)."""
import sys, os, time, csv
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from menu import construir_carta, aplanar, CartaPOS, Ticket, Migas, Categoria, Producto
from estrategias import ListaPlana, PorCategoria, Busqueda

RES = os.path.join(os.path.dirname(__file__), 'results')
os.makedirs(RES, exist_ok=True)
TAMANOS = [0, 5, 20, 60]  # extra por categoría → catálogos de distinto tamaño

def escalabilidad():
    estrategias = [ListaPlana(), PorCategoria(), Busqueda()]
    filas = []
    print('\n=== ESCENARIO A · ESCALABILIDAD (promedios sobre TODOS los productos) ===')
    print(f'{"Productos":>10} | ' + ' | '.join(f'{e.nombre:>22}' for e in estrategias))
    print('-'*90)
    for extra in TAMANOS:
        carta = construir_carta(extra_por_categoria=extra)
        objetivos = [p.nombre for p in aplanar(carta)]
        n = len(objetivos)
        cel = {}
        for e in estrategias:
            total_pasos = 0; t0 = time.perf_counter()
            for _ in range(20):  # repetir para medir tiempo con estabilidad
                for obj in objetivos:
                    _, pasos = e.buscar(carta, obj); total_pasos += pasos
            dt = (time.perf_counter()-t0)/(20*n)*1e6  # microsegundos por búsqueda
            avg = total_pasos/(20*n)
            cel[e.nombre] = (avg, dt)
        print(f'{n:>10} | ' + ' | '.join(f'{cel[e.nombre][0]:>10.1f} pasos' for e in estrategias))
        for e in estrategias:
            filas.append({'productos': n, 'estrategia': e.nombre,
                          'pasos_prom': round(cel[e.nombre][0],2), 'us_por_busqueda': round(cel[e.nombre][1],2)})
    with open(os.path.join(RES,'escalabilidad.csv'),'w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f, fieldnames=['productos','estrategia','pasos_prom','us_por_busqueda']); w.writeheader(); w.writerows(filas)
    print('\nLectura: la lista plana crece de forma lineal (O(n)); por categoría queda muy por debajo;')
    print('la búsqueda por índice se mantiene casi constante (O(1)). Es una mejora de escalabilidad.')
    _graficar(filas)
    return filas

def _graficar(filas):
    try:
        import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    except Exception as e:
        print('(matplotlib no disponible, se omite el gráfico:', e, ')'); return
    ns = sorted({f['productos'] for f in filas})
    fig, ax = plt.subplots(figsize=(7.5,4.2), dpi=150)
    for est in ['Lista plana','Por categoría','Búsqueda por texto']:
        ys=[next(f['pasos_prom'] for f in filas if f['productos']==n and f['estrategia']==est) for n in ns]
        ax.plot(ns, ys, marker='o', linewidth=2, label=est)
    ax.set_xlabel('Tamaño del catálogo (n.º de productos)'); ax.set_ylabel('Pasos promedio para llegar al producto')
    ax.set_title('Escalabilidad de la navegación del menú'); ax.legend(); ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(os.path.join(RES,'escalabilidad.png')); print('Gráfico →', os.path.join(RES,'escalabilidad.png'))

def validacion():
    print('\n=== ESCENARIO B · VALIDACIÓN + OBSERVER (navegar a "Capuchino") ===')
    carta = construir_carta(extra_por_categoria=20)
    ticket = Ticket(); migas = Migas(); pos = CartaPOS(carta).suscribir(ticket).suscribir(migas)
    objetivo = 'Capuchino'
    # localizar categoría y producto (Composite) + notificar (Observer)
    for cat in carta.subcategorias():
        for p in cat.productos():
            if p.nombre == objetivo:
                pos.notificar('navegacion', ['Carta', cat.nombre, p.nombre])
                pos.notificar('seleccion', p)
                break
    # comparar pasos de las tres estrategias para el mismo objetivo
    for e in (ListaPlana(), PorCategoria(), Busqueda()):
        _, pasos = e.buscar(carta, objetivo)
        print(f'  {e.nombre:>22}: {pasos} pasos')
    print('  Migas (Observer):', ' › '.join(migas.ruta))
    print('  Ticket (Observer):', [p.nombre for p in ticket.items], '— total $', ticket.total())
    ok = ticket.items and ticket.items[0].nombre == objetivo and migas.ruta[-1] == objetivo
    with open(os.path.join(RES,'validacion.txt'),'w',encoding='utf-8') as f:
        f.write(f'objetivo: {objetivo}\nmigas: {" > ".join(migas.ruta)}\nticket: {[p.nombre for p in ticket.items]}\n'
                f'total: {ticket.total()}\nvalidacion_ok: {bool(ok)}\n')
    print('  Validación OK:', bool(ok))

if __name__ == '__main__':
    modo = sys.argv[1] if len(sys.argv) > 1 else 'todo'
    if modo in ('todo','escalabilidad'): escalabilidad()
    if modo in ('todo','validacion'): validacion()
