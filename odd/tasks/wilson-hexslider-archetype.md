# Feature: Wilson Hexslider UI Archetype & Kernel Decoupling (Fase 5)
Implementación y formalización del arquetipo de interfaz gráfica 'kslider'
aplicado a la superficie microtonal hexagonal 2D (wilson.hexslider).

## Specs

- S1: "Adelante con eso" — Autorización para ejecutar la Fase 5 (Benchmark 2: wilson.hexslider).
- S2: Formalizar los contratos canónicos de `kslider` y `wilson.hexslider` en `core/schema/max_contracts.json` con tipado estricto de inlets, outlets y atributos.
- S3: Desacoplar el núcleo matemático y geométrico en un kernel C++17 puro (`benchmarks/teclados-wilson/wilson_hexslider_kernel.hpp`) libre de dependencias de Max SDK / JGraphics para cálculo de frecuencias EDO/ratios y hit-testing 2D.
- S4: Integrar el kernel desacoplado en `packages/wilson-suite/source/projects/wilson.hexslider/wilson.hexslider.cpp`.
- S5: Cosechar casos de prueba (`cases_hexslider.jsonl`) y verificar equivalencia semántica headless con `cpp_headless_runner.py`.
- S6: Ejecutar auditoría en vivo en Max 9 (`scripts/audit.py`) sobre `test_wilson_suite.maxpat` y verificar guardrail `scripts/check.py` al 100%.

## Tasks

- [x] T1 (S2) [inline]: Registrar contratos de `kslider` y `wilson.hexslider` en `core/schema/max_contracts.json` con pruebas unitarias en `tests/test_typed_patch.py`. Commit: d9e82c7
- [x] T2 (S3, S4) [inline]: Desacoplar `wilson_hexslider_kernel.hpp` con cálculo analítico de frecuencias y hit-testing euclidiano, e integrarlo en `wilson.hexslider.cpp`. Commit: 723a3b4
- [x] T3 (S5) [inline]: Implementar cosecha y diff semántico headless para `wilson_hexslider_kernel.hpp` con tests unitarios. Commit: dc62a66
- [x] T4 (S6) [inline]: Ejecutar Live Runtime Audit en Max 9 y verificar guardrail integral (`scripts/check.py`). Commit: 5d22875

## Log

- L1: "Adelante con eso" — Inicio de Fase 5: Benchmark 2 (wilson.hexslider) tras completar la Fase 3 de CI.
- L2: Live Max 9 runtime audit PASS (test_wilson_suite.maxpat) y guardrail scripts/check.py PASS (100% tests, schemas válidos, 0 leaks de privacidad).
