# Arquetipo Canónico: `kslider` (Max Piano Keyboard)

> **Propósito**: Servir como plantilla y contrato de comportamiento para cualquier objeto de interfaz que actúe como teclado o superficie de control cromática o microtonal en Max MSP (ej. `wilson.hexslider`, `micro.fretboard`).

---

## 1. Contrato de Interfaz

### Inlets (Entradas)
| Inlet # | Tipo | Función |
| :--- | :--- | :--- |
| **0 (Izquierdo)** | `int` / `list` | Número de nota MIDI entrante. Si entra un entero, resalta visualmente la tecla correspondiente y emite el valor por los outlets. Si entra una lista `(pitch, velocity)`, maneja el estado de note-on (vel > 0) o note-off (vel = 0). |
| **1 (Derecho)** | `int` | Velocidad asignada para las notas generadas al hacer clic con el mouse sobre el teclado. |

### Outlets (Salidas)
| Outlet # | Tipo | Función |
| :--- | :--- | :--- |
| **0 (Izquierdo)** | `int` / `float` | **Pitch**: Número de tecla/nota pulsada. En microtonalismo, este outlet puede emitir números de punto flotante (micro-cents) o ratios. |
| **1 (Derecho)** | `int` | **Velocity**: Velocidad de la pulsación (típicamente 0 a 127). Emite >0 en mouse-down / drag-enter, y 0 en mouse-up / drag-leave. |

---

## 2. Atributos Clave del Inspector (Inspector Properties)

1. **Rango y Offset**:
   - `offset`: Nota MIDI base de la tecla más grave (default: 36 / C1).
   - `range`: Cantidad total de teclas visibles (default: 48 / 4 octavas).
2. **Modo de Operación**:
   - `mode`: Monophonic (0), Polyphonic / Touch (1), Toggle (2).
3. **Estilo Visual**:
   - `whitekeycolor`, `blackkeycolor`, `activekeycolor`, `selectioncolor`.

---

## 3. Adaptación al Dominio Microtonal (`wilson.hexslider`)

Cuando el traductor de código enfrente una superficie como el teclado hexagonal de Erv Wilson (`Teclados-Wilson`):

| Característica | `kslider` Estándar | `wilson.hexslider` (Traducción Adaptada) |
| :--- | :--- | :--- |
| **Geometría** | Teclas rectangulares 1D (blancas/negras) | Celdas hexagonales 2D en retícula periódica |
| **Afinación** | Cromática fija 12-EDO (semitonos) | Afinación libre (CPS, Hexany, Eikosany, EDOs 31/41/53) |
| **Datos de Salida** | Enteros MIDI 0-127 | Par: (Ratio/Hz flotante, Velocity) + Mensaje MPE Pitch-Bend |
| **Inspector** | Octavas y desplazamiento MIDI | Factores generadores (A, B, C, D, E, F) y escala base |
