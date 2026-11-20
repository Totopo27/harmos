# Feature: Semantic Oracle, Provenance & Robustness (Rectificado)
Transferencia metodológica e ingeniería de compilación inspirada en rust-anything hacia Harmos.
Seguimiento ODD de tareas por commits unitarios atómicos.

## Specs

- S1: "vamos paso a paso realizando todas las implementaciones que sugieres, cuando tengas una hecha haz commit relacionado a esta, luego procede con la siguiente, así las vamos generando por commits, me parece más ordenado."
- S2: Sanear `scripts/audit.py` reemplazando `time.sleep(8)` por sondeo reactivo, abriendo en modo binario `"rb"` para evitar desalineación de bytes en Windows (`\r\n`), y usando marcadores centinela / resolución por versión exacta.
- S3: Implementar Huella de Procedencia Criptográfica (`emitted-from.json`) con hashes SHA-256 de fuentes, IR y `max_contracts.json` para detectar derivas y obsolescencia en parches emitidos.
- S4: Publicar declaración explícita de límites del oráculo (`docs/ORACULO_LIMITES.md`) y documentar el alcance real de `PASS` estructural vs. semántico (I11).
- S5: Implementar veredictos explícitos de aceptación en benchmarks (I6).
- S6: Desacoplar generador de C++ Min-Devkit: separar Kernel C++ Puro (`kernel.hpp`) de Binding Min-Devkit (`min_wrapper.cpp`) como prerrequisito para el oráculo headless.

## Tasks

- [x] T1 (S2) [inline]: Sanear `scripts/audit.py` (sondeo reactivo, lectura binaria `"rb"`, marcador centinela) y tests de auditoría. Commit: 75f9fe3
- [x] T2 (S3) [inline]: Implementar módulo de procedencia `emitted-from.json` y verificación en CLI. Commit: 06bcd03
- [x] T3 (S4) [inline]: Redactar declaración formal de límites del oráculo y honestidad epistémica (I11). Commit: eeda01f
- [x] T4 (S5) [inline]: Implementar veredictos explícitos en benchmarks (I6). Commit: pending
- [ ] T5 (S6) [inline]: Refactorizar emisión C++ desacoplando Kernel Puro y Binding Min-Devkit. Commit: pending

## Log

- L1: "ok, teniendo esto en cuenta, vamos paso a paso realizando todas las implementaciones que sugieres, cuando tengas una hecha haz commit relacionado a esta, luego procede con la siguiente, así las vamos generando por commits, me parece más ordenado."
- L2: "modifica el informe que hiciste con esto reciente y luego volvamos a retomar el trabajo"
