# Feature: Headless Semantic Oracle (Fase 2)
Implementación del oráculo de equivalencia semántica para Harmos:
Cosecha de casos (cases.jsonl), diff con tolerancia escalar y runner headless.

## Specs

- S1: "vamos con eso" (autorización para ejecutar Fase 2 tras la conclusión y estabilización de Fase 1).
- S2: Implementar especificación y cosechador de vectores de prueba (`cases.jsonl`) en `core/compiler/oracle_harvest.py` para capturar oráculos reproducibles desde suites existentes o funciones de referencia.
- S3: Implementar runner de `diff` semántico (`core/compiler/oracle_diff.py`) con comparación de tolerancias numéricas escalares (`tolerance`), detección de fallos y veredictos estructurados `PASS (SEMANTIC) / FAIL (MISMATCH)`.
- S4: Integrar subcomandos `harvest` y `diff` en `core/compiler/cli.py` y actualizar documentación de compuertas (`docs/ORACULO_LIMITES.md`).
- S5: Implementar soporte headless para compilar y ejecutar kernels C++ puros sin necesidad de Cycling '74 Max.

## Tasks

- [x] T1 (S2) [inline]: Implementar especificación y cosechador de casos `cases.jsonl` (`core/compiler/oracle_harvest.py`) y tests unitarios. Commit: 76e817e
- [x] T2 (S3) [inline]: Implementar runner de `diff` semántico con tolerancia numérica (`core/compiler/oracle_diff.py`) y tests unitarios. Commit: 4ce0eb5
- [x] T3 (S4) [inline]: Integrar comandos `harvest` y `diff` en la CLI de Harmos y actualizar compuertas. Commit: 54c65aa
- [x] T4 (S5) [inline]: Implementar arnés de prueba headless para kernels C++ desacoplados y validar contra benchmarks piloto. Commit: 195a8a2

## Log

- L1: "fase 2" — Inicio formal de la Fase 2 del roadmap arquitectónico tras estabilización y cierre de Fase 1.
