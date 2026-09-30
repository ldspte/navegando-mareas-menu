# -*- coding: utf-8 -*-
"""Navegando mareas — Escenario C: PRUEBA DE CARGA (latencia y throughput).

Aplica el método del arquitecto visto en clase
(Escenario → Métricas → Hipótesis → Evidencia → Decisión → Trade-off → Validación)
para *demostrar con evidencia* el cuello de botella de la navegación bajo carga y
*validar* la mejora con una NUEVA medición.

- Antes  = 'Lista plana'  (recorrido O(n)  → hipótesis de cuello de botella)
- Después = 'Búsqueda por texto' (índice hash O(1) → decisión arquitectónica)

Solo biblioteca estándar; matplotlib es opcional (solo para el gráfico).
Uso:  python carga.py
"""
import sys, os, io, time, csv, random, tracemalloc
from concurrent.futures import ThreadPoolExecutor
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from menu import construir_carta, aplanar
from estrategias import ListaPlana, Busqueda

RES = os.path.join(os.path.dirname(__file__), 'results')
os.makedirs(RES, exist_ok=True)

# Parámetros de la prueba de carga
EXTRA = 60          # catálogo grande (~557 productos)
SEC_REQS = 20000    # peticiones para la medición secuencial (latencia estable)
CLIENTES = 500      # clientes concurrentes (carga)
POR_CLIENTE = 50    # navegaciones por cliente  → 25 000 peticiones
WORKERS = 32        # hilos del pool


def percentil(datos, q):
    d = sorted(datos)
    if not d:
        return 0.0
    k = (len(d) - 1) * q / 100.0
    f = int(k); c = min(f + 1, len(d) - 1)
    if f == c:
        return d[f]
    return d[f] + (d[c] - d[f]) * (k - f)


def _resumen(nombre, modo, lat, thr):
    return {
        'estrategia': nombre, 'modo': modo, 'n_peticiones': len(lat),
        'p50_ms': round(percentil(lat, 50), 4),
        'p95_ms': round(percentil(lat, 95), 4),
        'p99_ms': round(percentil(lat, 99), 4),
        'throughput_rps': round(thr, 0),
    }


def medir_secuencial(estrategia, carta, objetivos, reqs):
    estrategia.buscar(carta, objetivos[0])          # pre-calentar (índice amortizado)
    lat = []
    t0 = time.perf_counter()
    for i in range(reqs):
        obj = objetivos[i % len(objetivos)]
        a = time.perf_counter()
        estrategia.buscar(carta, obj)
        lat.append((time.perf_counter() - a) * 1000.0)   # ms
    wall = time.perf_counter() - t0
    return lat, reqs / wall


def medir_concurrente(estrategia, carta, objetivos, clientes, por_cliente):
    estrategia.buscar(carta, objetivos[0])          # pre-calentar
    def tarea(cid):
        loc = []
        for i in range(por_cliente):
            obj = objetivos[(cid + i) % len(objetivos)]
            a = time.perf_counter()
            estrategia.buscar(carta, obj)
            loc.append((time.perf_counter() - a) * 1000.0)
        return loc
    t0 = time.perf_counter()
    lat = []
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for loc in ex.map(tarea, range(clientes)):
            lat.extend(loc)
    wall = time.perf_counter() - t0
    return lat, len(lat) / wall


def costo_indice(carta, objetivos):
    """Trade-off: cuánto cuesta (tiempo y memoria) construir el índice hash."""
    b = Busqueda()
    tracemalloc.start()
    t0 = time.perf_counter()
    idx = b._indexar(carta)
    build_ms = (time.perf_counter() - t0) * 1000.0
    _, pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return build_ms, len(idx), pico / 1024.0  # ms, entradas, KiB


def main():
    carta = construir_carta(extra_por_categoria=EXTRA)
    objetivos = [p.nombre for p in aplanar(carta)]
    random.seed(7); random.shuffle(objetivos)
    n = len(objetivos)

    print('=' * 78)
    print(f'ESCENARIO C · PRUEBA DE CARGA — navegación del menú ({n} productos)')
    print('=' * 78)
    print('1) ESCENARIO   : la carta crece y muchos cajeros/clientes navegan a la vez.')
    print('2) MÉTRICAS    : latencia p50/p95/p99 (ms) y throughput (peticiones/s).')
    print('3) HIPÓTESIS   : el cuello de botella es el recorrido O(n) de la lista plana.')
    print('4) EVIDENCIA   : se mide ANTES (lista plana) y se compara con DESPUÉS (índice).')

    filas = []
    antes = ListaPlana()
    despues = Busqueda()

    # --- Secuencial ---
    lat_a, thr_a = medir_secuencial(antes, carta, objetivos, SEC_REQS)
    lat_d, thr_d = medir_secuencial(despues, carta, objetivos, SEC_REQS)
    filas.append(_resumen('Lista plana (antes)', 'secuencial', lat_a, thr_a))
    filas.append(_resumen('Índice hash (después)', 'secuencial', lat_d, thr_d))

    # --- Concurrente (carga) ---
    latc_a, thrc_a = medir_concurrente(antes, carta, objetivos, CLIENTES, POR_CLIENTE)
    latc_d, thrc_d = medir_concurrente(despues, carta, objetivos, CLIENTES, POR_CLIENTE)
    filas.append(_resumen('Lista plana (antes)', f'concurrente x{CLIENTES}', latc_a, thrc_a))
    filas.append(_resumen('Índice hash (después)', f'concurrente x{CLIENTES}', latc_d, thrc_d))

    build_ms, entradas, kib = costo_indice(carta, objetivos)

    # --- Salida ---
    print('\n5) DECISIÓN    : sustituir el recorrido lineal por un índice hash (Strategy).')
    print('6) TRADE-OFF   : el índice cuesta memoria y un armado inicial:')
    print(f'                 armado {build_ms:.2f} ms · {entradas} entradas · ~{kib:.0f} KiB (una sola vez, amortizado).')
    print('7) VALIDACIÓN  : nueva medición tras el cambio →')
    hdr = f'{"métrica":<26}{"ANTES (O(n))":>16}{"DESPUÉS (O(1))":>16}{"mejora":>12}'
    print('\n' + hdr); print('-' * len(hdr))
    def linea(nom, a, d, unidad, mejora_como='baja'):
        if mejora_como == 'baja':
            factor = f'{a/d:.0f}x menos' if d else '—'
        else:
            factor = f'{d/a:.0f}x más' if a else '—'
        print(f'{nom:<26}{a:>13.3f} {unidad:<2}{d:>13.3f} {unidad:<2}{factor:>12}')
    p95_a = percentil(latc_a, 95); p95_d = percentil(latc_d, 95)
    linea('Latencia p95 (carga)', p95_a, p95_d, 'ms', 'baja')
    linea('Throughput (carga)', thrc_a, thrc_d, '/s', 'sube')

    with open(os.path.join(RES, 'carga.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['estrategia', 'modo', 'n_peticiones',
                                          'p50_ms', 'p95_ms', 'p99_ms', 'throughput_rps'])
        w.writeheader(); w.writerows(filas)

    with open(os.path.join(RES, 'carga.txt'), 'w', encoding='utf-8') as f:
        f.write(f'ESCENARIO C - PRUEBA DE CARGA ({n} productos)\n')
        f.write(f'Hipotesis: el cuello de botella es el recorrido O(n) de la lista plana.\n')
        f.write(f'Trade-off del indice: armado {build_ms:.2f} ms, {entradas} entradas, ~{kib:.0f} KiB (una vez).\n\n')
        for r in filas:
            f.write(f"{r['modo']:>18} | {r['estrategia']:<24} | p50={r['p50_ms']:.4f} ms "
                    f"p95={r['p95_ms']:.4f} ms p99={r['p99_ms']:.4f} ms | {r['throughput_rps']:.0f} req/s\n")
        f.write(f"\nVALIDACION (bajo carga): p95 {p95_a:.3f} -> {p95_d:.3f} ms; "
                f"throughput {thrc_a:.0f} -> {thrc_d:.0f} req/s.\n")

    _graficar(filas, p95_a, p95_d, thrc_a, thrc_d)
    print('\nArchivos → results/carga.csv, results/carga.txt, results/carga.png')
    return filas


def _graficar(filas, p95_a, p95_d, thr_a, thr_d):
    try:
        import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    except Exception as e:
        print('(matplotlib no disponible, se omite el gráfico:', e, ')'); return
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 4), dpi=150)
    et = ['Antes\n(O(n))', 'Después\n(O(1))']
    ax1.bar(et, [p95_a, p95_d], color=['#c0392b', '#27ae60'])
    ax1.set_title('Latencia p95 bajo carga (ms)'); ax1.set_ylabel('ms (menos es mejor)')
    for i, v in enumerate([p95_a, p95_d]):
        ax1.text(i, v, f'{v:.3f}', ha='center', va='bottom', fontsize=9)
    ax2.bar(et, [thr_a, thr_d], color=['#c0392b', '#27ae60'])
    ax2.set_title('Throughput bajo carga (peticiones/s)'); ax2.set_ylabel('req/s (más es mejor)')
    for i, v in enumerate([thr_a, thr_d]):
        ax2.text(i, v, f'{v:,.0f}', ha='center', va='bottom', fontsize=9)
    fig.suptitle('Navegando mareas — validación del cambio arquitectónico', fontweight='bold')
    fig.tight_layout(); fig.savefig(os.path.join(RES, 'carga.png'))
    print('Gráfico →', os.path.join(RES, 'carga.png'))


if __name__ == '__main__':
    main()
