---
name: tet-inversion-geometry-expert
description: "Trigger: tet-inversion, tet-symmetry, parejas inversion, puntos fijos n-TET. Audita geometría de simetría y descomposición de pares 3-72 TET en Max MSP."
license: Apache-2.0
metadata:
  author: "OptimizandoParaMaxSDK"
  version: "2.1"
---

# TET Inversion Geometry Expert

## Activation Contract

Cargar al analizar, portar o implementar objetos de Max MSP dedicados a simetrías de inversión, partición de clases de alturas en pares $(i, \text{partner})$ y cálculo de puntos fijos en sistemas $n$-TET (3 a 72 divisiones por octava).

## Hard Rules

- **Aritmética Modular Estricta**: Aplicar siempre $\text{mod}(n, m) = ((n \pmod m) + m) \pmod m$ para prevenir residuos negativos.
- **Determinismo en Pares y Puntos Fijos**: Para suma de índices $S$ y $T$ divisiones, resolver $\text{partner}(i) = \text{mod}(S - i, T)$.
  - Si $\text{partner}(i) == i$: registrar como Punto Fijo (eje de simetría invariante).
  - Si $\text{partner}(i) \neq i$: registrar como Par de Inversión $[i, \text{partner}(i)]$ exactamente una vez (sin duplicados simétricos).
- **Cero Hardcoding**: Los parámetros $T \in [3, 72]$ y $S \in [0, T-1]$ deben ser atributos dinámicos modificables en caliente vía inlets o inspectores de Max.
- **Control Bézier en Coordenadas Polares**: Calcular puntos de control $(cx, cy)$ evaluando distancia angular mínima y factor proporcional de curvatura hacia el centro del círculo.

## Decision Gates

| Condición de $T$ | Puntos Fijos para Suma $S$ | Eje de Simetría Resultante |
| :--- | :--- | :--- |
| **$T$ Par** (ej. 12, 24, 72) | 0 o 2 puntos fijos según paridad de $S$ | Pasa por dos notas diametrales o dos puntos medios |
| **$T$ Impar** (ej. 19, 31, 41, 53) | Exactamente 1 punto fijo para todo $S$ | Pasa por una nota y por el punto medio opuesto |

## Execution Steps

1. Validar parámetros entrantes $T \in [3, 72]$ y suma de índices $S \in [0, T-1]$.
2. Iterar índices $i \in [0, T-1]$ y calcular $\text{partner}(i)$ mediante aritmética modular.
3. Clasificar cada nota en Punto Fijo o Par de Inversión único.
4. Calcular arcos Bézier cuadráticos en coordenadas polares para renderizado vectorial en JGraphics o `jsui`.
5. Formatear y emitir listas estructuradas de átomos de Max (`t_atom`).

## Output Contract

- Lista estructurada de pares de inversión únicos `[i, partner]` y puntos fijos `[p1, ...]`.
- Coordenadas polares/Bézier y frecuencias microtonales listas para síntesis y visualización.

## References

- `references/inversion-geometry.md` — Derivaciones matemáticas de simetría modular, paridad de ejes y arcos Bézier.
