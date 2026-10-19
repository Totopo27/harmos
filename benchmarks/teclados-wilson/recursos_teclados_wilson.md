# Perfil Técnico de Dominio: Teclados-Wilson
> Generado por `max-project-scout`

## 1. Inventario del Proyecto Fuente
- **Proyecto de referencia**: Teclados-Wilson (caso piloto microtonal)
- **Naturaleza del Stack**: JavaScript clásico (Vanilla JS), HTML5, SVG dinámico y CSS.
- **Sin dependencias pesadas de NPM**: Lógica pura basada en arreglos, funciones recursivas de combinatoria y manipulación de coordenadas geométricas.

---

## 2. Descomposición de la Lógica Pura (Agnóstica a la Web)

### Módulo A: Motor Matemático Armónico (Harmonic & Tuning Core)
- **Archivos clave**: `hexany-data.js`, `eikosany-data.js`, `monany-data.js`, `dalessandro.js`, `edo31.js`, `edo41.js`, `edo53.js`.
- **Algoritmo central**: 
  - Cálculo de Combinaciones de Factores Primos $k$ de $n$: Función `getCombinations(arr, k)`.
  - Generación de subconjuntos de escalas de Wilson: Pentanies (1)5), Tetranies (1)4), Trianies (1)3) y Dyanies (1)2).
  - Normalización de ratios dentro de la octava ($1.0 \le ratio < 2.0$).
  - Conversión a grados microtonales y cents.
- **Clasificación de Destino en Max**: **C++ Control External (`min.object`)** o **Max Native Abstraction** con lookups en `coll`/`dict`.

### Módulo B: Motor Geométrico de Teclado Hexagonal (HexGrid Engine)
- **Archivos clave**: `hexgrid.js`.
- **Algoritmo central**:
  - Retícula periódica flat-top de celdas hexagonales ($39 \times 25 = 975$ celdas).
  - Cálculo de coordenadas axiales y de pantalla:
    - $x = \text{col} \times (\text{size} \times 1.5)$
    - $y = \text{row} \times (\text{size} \times \sqrt{3}) + (\text{col \% 2} == 1 ? \text{size} \times \frac{\sqrt{3}}{2} : 0)$
  - Mapeo de celda $(col, row) \rightarrow$ Frecuencia / Grado de nota / Color de zona.
- **Clasificación de Destino en Max**: **Arquetipo `kslider` extendido (`wilson.hexslider`)** implementado mediante **JGraphics C++** o **JS Painter (`mgraphics`)**.

---

## 3. Mapeo Canónico con Max (Evitar Reinvención)
1. **Generación de Sonido**: Max ya cuenta con `cycle~`, `poly~`, `groove~`. El proyecto Wilson **no** debe generar audio internamente; debe emitir mensajes de notas y frecuencias por sus outlets hacia objetos estándar de Max.
2. **Envío MIDI / MPE**: Max ya tiene `xbendout`, `midiformat` y `noteout`. `wilson.hexslider` debe emitir listas `(frecuencia_hz, velocity)` o pares `(nota_midi, pitchbend_cents)`.
3. **Persistencia de Escalas**: Usar `dict` o `coll` de Max para almacenar las tablas de notas precalculadas.

---

## 4. Skills Requeridas para Generación
La `max-skill-factory` debe generar la skill especializada:
- `wilson-tuning-auditor`: Reglas de combinatoria de factores primos de Wilson y validación de ratios armónicos exactos.
