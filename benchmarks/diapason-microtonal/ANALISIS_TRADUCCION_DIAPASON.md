# Análisis de Portabilidad del Traductor: Diapason-microtonal hacia Max MSP

> **Dictamen del Meta-Traductor**: Aplicación de la metodología de descomposición atómica y adaptación del arquetipo de interfaz de mástil para Max MSP.

---

## 1. Inventario del Proyecto `Diapason-microtonal`
- **Proyecto de referencia**: Diapason-microtonal (benchmark de modelado físico de mástil)
- **Stack original**: React 19, TypeScript, Vite, SVG/CSS.
- **Lógica Pura Aislada**:
  - `src/core/math/physics.ts`: Ecuación física de posición de traste en milímetros desde la cejuela (*nut*):
    $$L_2 = L_1 \times \left(\frac{f_1}{f_2}\right)$$
    $$\text{pos} = \text{scaleLength} - L_2$$
    con compensación dinámica de tensión/altura de acción (*True Temperament approximation*).
  - Modelado de cuerdas: Afinación base por cuerda, calibre (*gauge*), tensión y longitud de escala (ej. 650 mm).
  - Mapeo de trastes a frecuencias de entonación justa / armónicos.

---

## 2. Descomposición Atómica para Max MSP

En Max no creamos un componente web React; creamos dos objetos modulares:

### Objeto 1: `micro.fretmath` (C++ Control External)
- **Responsabilidad**: Calcula las posiciones físicas de los trastes en milímetros y sus frecuencias asociadas.
- **Inlet 0**: Mensajes de configuración (longitud de escala, afinación de cuerda base, lista de ratios o divisiones EDO).
- **Outlets**:
  - **Outlet 0**: Lista de posiciones en mm de cada traste.
  - **Outlet 1**: Lista de frecuencias en Hz asociadas a cada traste.
- **Arquetipo**: Matemático puro (similar a `expr` o `scale`).

### Objeto 2: `micro.fretboard` (C++ UI External con JGraphics)
- **Responsabilidad**: Dibuja el mástil de guitarra/bajo interactivo con cuerdas horizontales y líneas de trastes microtonales (curvadas si usa True Temperament).
- **Arquetipo**: Adaptación de `kslider` pero con coordenadas 2D (Cuerda $\times$ Traste):
  - **Inlet 0**: Control y resaltado de trastes/cuerdas.
  - **Inlet 1**: Velocity.
  - **Outlet 0 (izquierdo)**: Frecuencia en Hz al pulsar una cuerda/traste.
  - **Outlet 1**: Velocity (Note-On >0, Note-Off 0).
  - **Outlet 2**: Metadatos `[cuerda_id, traste_id, mm_pos]`.
- **Integración Inmediata**: La salida de `micro.fretboard` se conecta directo al objeto **`micro.mpe`** que ya creamos, sonando en Reaper/sintes al instante.
