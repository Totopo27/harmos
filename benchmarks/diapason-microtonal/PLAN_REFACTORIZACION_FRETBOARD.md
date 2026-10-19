# Plan de Refactorización de Dominio: `micro.fretboard` Fiel a Tolgahan Çoğulu

> **Objetivo**: Elevar `micro.fretboard` de un mástil genérico a un instrumento de modelado físico microtonal auténtico basado en el caso piloto `Diapason-microtonal`.

---

## 1. Arquitectura de Mástil Fretlet (Trastes Modulares por Cuerda)

En una guitarra microtonal real (como la de Çoğulu):
1. **8 Cuerdas Reales**:
   - Cuerda 1 (E4: 330 Hz)
   - Cuerda 2 (B3: 247.5 Hz)
   - Cuerda 3 (G3: 198 Hz)
   - Cuerda 4 (D3: 148.5 Hz)
   - Cuerda 5 (A2: 110 Hz)
   - Cuerda 6 (E2: 82.5 Hz)
   - Cuerda 7 (D2: 74.25 Hz)
   - Cuerda 8 (C2: 66 Hz)
2. **Fretlets Segmentados Independientes**:
   - Cada cuerda tiene su propia ranura donde los trastes no son barras completas, sino pequeños bloques deslizables (*fretlets*).
   - El dibujo vectorial en JGraphics debe renderizar el canal guía de cada cuerda y los fretlets posicionados sobre la cuerda correspondiente.
3. **Sistemas de Afinación Nativos de Dominio**:
   - **`dalessandro`**: 42 notas por octava basadas en ratios Wilson.
   - **`partch`**: 43 notas por octava (límite 11 de Entonación Justa).
   - **`12tet`**: 12 notas estándar de referencia.
   - **`edo`**: Divisiones iguales parametrizables (31, 41, 53).
4. **Modo Polifónico / Acordes (Chord Mode)**:
   - Capacidad de mantener notas presionadas en diferentes cuerdas simultáneamente.
   - Emisión polifónica MPE por canal independiente de cuerda (Cuerda 1 $\rightarrow$ Canal 2, Cuerda 2 $\rightarrow$ Canal 3 ... Cuerda 8 $\rightarrow$ Canal 9).
