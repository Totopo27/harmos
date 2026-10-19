# Análisis de Portabilidad del Traductor: generadorTETAnalisisCirculos hacia Max MSP (Versión Actualizada React/Vite/TS)

> **Dictamen del Meta-Traductor**: Descomposición atómica y evaluación de viabilidad de interfaz para el Generador de Círculos TET con análisis de simetrías, suma de índices y mapas de inversión (3 a 72 TET).

---

## 1. Ficha Técnica del Proyecto Actualizado
- **Proyecto de referencia**: generadorTETAnalisisCirculos (caso piloto de geometría modular)
- **Stack**: React 18, TypeScript 5.5, Vite 5.4, Tailwind CSS, Lucide React.
- **Suite de Pruebas**: 5 tests en `src/utils/tet-math.test.ts` ejecutados con `tsx --test` (100% pasando).
- **Dominio Teórico**: Geometría de grupos cíclicos $\mathbb{Z}_n$, partición en involuciones (inversiones) y ejes de simetría en afinaciones microtonales $n$-TET ($3 \le n \le 72$).

---

## 2. Inventario de Capacidades y Lógica Aislada

### A. Núcleo Matemático y Geometría (`src/utils/tet-math.ts`)
1. **Aritmética modular euclidiana**: `mod(n, m) = ((n % m) + m) % m`.
2. **Generador de Pares de Inversión y Puntos Fijos**: `getInversionPairs(divisions, indexSum)`.
   - Para cualquier suma de índices $S$, calcula los pares simétricos $[i, (S - i) \pmod T]$ y detecta los puntos fijos donde $i = (S - i) \pmod T$.
   - Propiedad geométrica clave:
     - En temperamentos impares ($T \in \{19, 31, 41, 53\}$) siempre hay exactamente 1 punto fijo.
     - En temperamentos pares ($T \in \{12, 24, 72\}$) hay 0 o 2 puntos fijos según la paridad de $S$.
3. **Cálculo de Curvatura Bézier**: `calculateCurvature(i, partner, divisions, circleRadius)`.
   - Determina el punto de control $(cx, cy)$ para trazar arcos internos entre notas simétricas con factor de curvatura dinámico.
4. **Escala tipográfica adaptativa**: `calculateFontSize(divisions)`.

### B. Modos Interactivos y UI
1. **Modo Círculo Individual (`TETSingleCircle`)**:
   - Círculo de notas con marcas radiales, numeración adaptativa, curvas Bézier conectando parejas simétricas y puntos fijos en rojo.
2. **Modo Página Múltiple (`TETInversionGrid`)**:
   - Generación de grillas con todas las inversiones $I_0, I_1, \dots, I_{k}$ simultáneas.
3. **Exportación Vectorial SVG**:
   - Descarga directa de archivos SVG para publicaciones o análisis analítico.

---

## 3. Compuerta de Viabilidad de Interfaz (UI Feasibility Gate)

### Evaluación de Opciones Técnicas en Max MSP:
- **Ruta A (Nativa C++ Min-Devkit / JGraphics)**:
  - Dibujar arcos Bézier cuadráticos con JGraphics (`jgraphics_curve_to`) es posible para un círculo único, pero recrear toda la grilla interactiva, controles deslizantes y exportación vectorial en C++ exigiría miles de líneas y mantenimiento rígido.
- **Ruta B (Estrategia Híbrida v2.0 Recomendada)**:
  - **Módulo Lógico y Matemático (`tet.inversion`)**: Objeto de Max (implementado en Max JS o external C++) que procesa las divisiones $T$ y la suma de índices $S$, emitiendo las listas de pares $[i, partner]$, los puntos fijos y las frecuencias correspondientes en Hz hacia el motor DSP de Max.
  - **Módulo Visual / Interactivo (`jweb`)**: Embebe la aplicación React/Vite directamente en Max MSP, permitiendo la exploración visual completa con Reactivo 1:1, exportación SVG y modo oscuro/claro.
  - **Puente de Control**: Enlace bidireccional mediante mensajes Max / OSC para que al mover los controles en Max o en la web, el motor de sonido y el visualizador se sincronicen en tiempo real.

---

## 4. Contrato de Inlets / Outlets para `tet.inversion`

```json
{
  "inlets": {
    "0": { "name": "index_sum", "type": "int", "description": "Suma de índices S para inversión I_xy" },
    "1": { "name": "divisions", "type": "int", "description": "Divisiones n-TET (3 a 72)" },
    "2": { "name": "base_freq", "type": "float", "description": "Frecuencia base C4 en Hz" }
  },
  "outlets": {
    "0": { "name": "pairs_list", "type": "list", "description": "Lista aplanada de pares [i, partner, ...]" },
    "1": { "name": "fixed_points", "type": "list", "description": "Lista de puntos fijos" },
    "2": { "name": "fixed_frequencies", "type": "list", "description": "Frecuencias de los puntos fijos en Hz" },
    "3": { "name": "symmetry_count", "type": "int", "description": "Cantidad de pares calculados" }
  }
}
```

---

## 5. Dictamen de Validación
- **Paridad Funcional**: 100% alcanzable.
- **Cero Hardcoding**: Rangos y sumas de índices completamente dinámicos.
- **Próximas Acciones**:
  1. Registrar contrato en `core/schema/max_contracts.json`.
  2. Implementar `tet_inversion.js` y verificar contra los 5 casos de prueba de `src/utils/tet-math.test.ts`.
  3. Desplegar patcher de integración `tet_inversion_suite.maxpat`.
