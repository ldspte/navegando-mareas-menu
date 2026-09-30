# Navegando mareas · Navegación eficiente del menú del restaurante

Prototipo para la actividad **«Navegando mareas: Estrategias de navegación en la
arquitectura de software»** · Arquitectura de Software · Unidad 3.

**Equipo:** Luis Fredy Pardo Lozano · Fabián David Pérez López · Ángela María Pizo Rojas
**Docente:** Edward Alfonso Villamizar Vallejo · Tecnológica del Oriente

**Entregables:** informe técnico (PDF) · presentación (deck) · **video:** _pega aquí el enlace de YouTube (no listado)_

---

## El problema de navegación

En el punto de venta de un restaurante, la **carta** crece con el tiempo (más platos,
más bebidas, más panadería). Con una **lista plana** el cajero debe recorrerla de arriba
abajo para hallar un producto: cuanto más grande el catálogo, más tarda —no escala—. El
reto es **encontrar cualquier producto en pocos pasos y que ese esfuerzo no crezca** al
crecer la carta.

## Estrategias y patrones de diseño

| Patrón | Dónde | Por qué |
|---|---|---|
| **Composite** | `menu.py` (`Categoria`/`Producto`) | La carta es un árbol: Carta › Categoría › Producto; nodos y hojas se tratan igual |
| **Iterator** | `menu.py` (`IteradorMenu`) | Recorre el árbol sin exponer su estructura y cuenta los nodos visitados |
| **Strategy** | `estrategias.py` | Intercambia el algoritmo de navegación: lista plana, por categoría o búsqueda por índice |
| **Observer** | `menu.py` (`CartaPOS`/`Ticket`/`Migas`) | El ticket y las migas de pan reaccionan a la navegación y a la selección |

## Cómo ejecutar

Requiere **Python 3.8+**. `matplotlib` es opcional (solo para los gráficos).

```bash
python run.py                # escenarios A (escalabilidad) y B (validación + Observer)
python run.py escalabilidad  # solo escalabilidad
python run.py validacion     # solo validación + observer
python carga.py              # escenario C: prueba de carga (latencia y throughput)
```

Genera en `results/`: `escalabilidad.csv`, `escalabilidad.png`, `validacion.txt`,
`carga.csv`, `carga.txt` y `carga.png`.

## Resultados de referencia

### A · Escalabilidad — pasos promedio para llegar a un producto

| Productos | Lista plana | Por categoría | Búsqueda por texto |
|---:|---:|---:|---:|
| 17  | 9.0   | 6.7  | 2.0 |
| 62  | 31.5  | 9.0  | 2.0 |
| 197 | 99.0  | 16.5 | 2.0 |
| 557 | 279.0 | 36.5 | 2.0 |

La lista plana crece de forma **lineal (O(n))**; navegar **por categoría** (Composite) queda
muy por debajo; y la **búsqueda por índice** se mantiene **constante (O(1))**.

### B · Validación + Observer

Navegar a «Capuchino» en una carta de ~200 productos: lista plana **89** pasos, por
categoría **8**, búsqueda **2**. Las migas muestran `Carta › Bebidas calientes › Capuchino`
y el ticket registra el producto ($6.500).

### C · Prueba de carga — latencia y throughput (500 clientes concurrentes, 557 productos)

| Escenario | Estrategia | Latencia p95 | Throughput |
|---|---|---:|---:|
| Antes  | Lista plana (O(n)) | 0,210 ms | 9.616 req/s |
| Después | Índice hash (O(1)) | 0,001 ms | 637.354 req/s |
| **Mejora** | | **262× menos** | **66× más** |

**Trade-off:** el índice cuesta ~93 KiB (557 entradas) y un armado inicial de ~2 ms, **una
sola vez** (amortizado). La optimización se **cierra con una nueva medición**.

## Evaluación (método del arquitecto · ATAM)

El cambio se sustenta con el método visto en clase —contrastar la arquitectura con
**atributos de calidad y escenarios** (ATAM)— en siete etapas:

1. **Escenario** — la carta crece y varios cajeros/clientes navegan a la vez.
2. **Métricas** — latencia p95 y throughput.
3. **Hipótesis** — el cuello de botella es el recorrido O(n) de la lista plana.
4. **Evidencia** — `carga.py` (500 clientes concurrentes) + perfilado de pasos.
5. **Decisión** — índice hash O(1) encapsulado como estrategia (Strategy).
6. **Trade-off** — memoria del índice y armado inicial (amortizado).
7. **Validación** — nueva medición: p95 262× menor, throughput 66× mayor.

## Estructura

```
navegando-mareas-menu/
├── run.py                 # escenarios A y B + métricas + resultados
├── carga.py               # escenario C: prueba de carga (latencia/throughput)
├── requirements.txt
├── README.md
├── results/               # csv, png, txt de los tres escenarios
└── src/
    ├── menu.py            # Composite + Iterator + Observer + builder de la carta
    └── estrategias.py     # Strategy: lista plana, por categoría, búsqueda por índice
```

## Mapa a la rúbrica

- **Problema de navegación** → carta extensa de un POS; encontrar productos sin que el esfuerzo crezca.
- **Modelado UML** → diagramas de componentes, clases, secuencia y actividad (en el informe).
- **Patrones de diseño** → Composite, Iterator, Strategy y Observer (tabla anterior).
- **Prototipo y pruebas** → `run.py` (pasos y tiempo) y `carga.py` (latencia y throughput bajo carga).
- **Evaluación** → método del arquitecto + ATAM, con hipótesis, evidencia, trade-offs y validación.
