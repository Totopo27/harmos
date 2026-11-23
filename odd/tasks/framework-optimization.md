# Feature: Harmos Framework Comprehensive Optimization
Resolución integral de los 77 hallazgos de auditoría a través de 5 fases de hardening,
refactorización arquitectónica, contratos estrictos, calidad de tests y documentación.

## Specs

- S1: "ve una por una resolviendo absolutamente todas las fases con los puntos de mejora que encontraste" — Autorización explícita para ejecutar las 5 fases de optimización.
- S2: Corregir `assess_connection()` en `core/compiler/contract_engine.py` para validar restricciones bidireccionales de tipos: prohibir cables de audio signal a message/control inlets y control a signal-only inlets a menos que se declare soporte union explícito.
- S3: Implementar resolución dinámica de aridad en `ContractEngine` para objetos de argumentos variables (`unpack`, `pack`, `trigger`, `route`, `poly~`).
- S4: Eliminar violaciones de Zero Hardcoding en `tests/test_poly_typed_patch.py`, reemplazando índices físicos numéricos por resolución semántica.
- S5: Hacer deterministas los tests flaky y dependientes del entorno en `tests/test_benchmark.py`, `tests/test_real_sc_ingestion.py` y `tests/test_sc_control_extractor.py`.
- S6: Añadir compuerta de verificación formal de contratos (`audit_contracts`) a patchers sintetizados en tests (`test_sc_voice_compiler.py`, `test_diesis_rosa_main.py`, `test_cli.py`).
- S7: Corregir nombres de outlets de `trigger` (t) en `max_contracts.json` alineándolos con la convención física de izquierda a derecha.
- S8: Añadir puertos faltantes auténticos de Max en `gain~`, `coll`, `scale` y soportar tipos de unión signal/float en primitivas MSP.
- S9: Añadir soporte de tipos `bang` y `number` en `max_object_ir.schema.json` y validar IR en `ContractEngine.from_ir()`.
- S10: Optimizar rendimiento de `ContractEngine` pre-normalizando puertos e indexando aliases semánticos en O(1) durante la carga del catálogo.
- S11: Estandarizar mensajes de error y diagnósticos en inglés identificando el objeto y rango permitido en fallos de contrato.
- S12: Expandir catálogo con primitivas estándar (`comment`, `number`, `dac~`, `adc~`, `metro`, `toggle`, etc.).
- S13: Blindar `scripts/check.py` con anclaje a `_REPO_ROOT`, escaneo fail-closed ante errores de git, y soporte de rutas macOS en PII scan.
- S14: Robustecer `scripts/audit.py` (evitar barrido de letras de unidad A-Z, detección de Max en macOS, cierre de árbol de procesos) y limpiar `scripts/bench.py`.
- S15: Integrar linting (`ruff`), chequeo de tipos (`mypy`) y reporte de cobertura (`coverage`) en CI y scripts.
- S16: Añadir paso de compilación E2E de IR a Max Package en CI.
- S17: Expandir matriz de CI con runner macOS y Python 3.12.
- S18: Restaurar la estricta separación de dominios de ADR-0001 desacoplando el arnés de test C++ (`cpp_headless_runner.py`) de los kernels de benchmark downstream.
- S19: Desacoplar código de dominio microtonal (`microtonal_engine.py`, `truax_kernel.hpp`, benchmarks SCLang) del core hacia módulos o suites downstream especializadas.
- S20: Descomponer las 8 funciones monolíticas identificadas (>100 líneas) en submódulos o helpers con responsabilidad única.
- S21: Deduplicar implementaciones de Truax Normal Form, resolución de paths canónicos y boilerplate de excepciones en generadores.
- S22: Optimizar `export_as_coll()` con evaluación perezosa y mitigar la latencia de muestreo de timer en `benchmark.py`.
- S23: Limpiar dead code, variables huérfanas y 11 imports no utilizados en `core/compiler/`.
- S24: Re-escribir `ARQUITECTURA_TRADUCTOR_MAX.md`, `FLUJO_DE_TRABAJO.md` y `README.md` reflejando el pipeline real del compilador determinista de Python y compuertas ODD.
- S25: Redactar ADRs 0006 a 0011 formalizando el Motor de Procedencia Criptográfica, Oráculo Semántico Headless, Arquitectura C++ Desacoplada, Generador Maxref XML, Motor de Contratos Tri-State, y Orden de Compuertas Estáticas.
- S26: Actualizar `GLOSSARY.md` con los 9 conceptos arquitectónicos faltantes.
- S27: Marcar `catalog/max_primitives.json` como obsoleto en favor de `core/schema/max_contracts.json`.
- S28: Añadir archivo `LICENSE` (Apache-2.0) y limpiar tareas ODD históricas.

## Tasks

- [x] T1 (S1-S6) [inline]: Fase 1 — Cimientos Críticos: Validación bidireccional en assess_connection, aridad dinámica en ContractEngine, corrección de zero-hardcoding en tests, tests herméticos/deterministas y compuerta de auditoría en patchers sintetizados. Commit: c4e8281
- [ ] T2 (S7-S12) [inline]: Fase 2 — Endurecimiento de Esquemas y Contratos: Corrección de puertos trigger/gain~/coll/scale, uniones signal/float, validación de IR, lookup O(1) pre-normalizado, primitivas base y diagnósticos unificados.
- [ ] T3 (S13-S17) [inline]: Fase 3 — Robustecimiento de CI/CD y Scripts: Blindaje fail-closed de check.py, audit.py multiplataforma, bench.py, integración de ruff/mypy/coverage en CI y pipeline E2E.
- [ ] T4 (S18-S23) [inline]: Fase 4 — Refactorización y Separación de Dominios: Desacoplamiento de kernels downstream de cpp_headless_runner, modularización de funciones monolíticas, lazy evaluation en microtonal_engine, optimización de benchmarking y eliminación de dead code.
- [ ] T5 (S24-S28) [inline]: Fase 5 — Gobernanza y Documentación Arquitectónica: Sincronización de README y arquitectura con el compilador real, redacción de ADRs 0006-0011, actualización de GLOSSARY.md, licenciamiento Apache-2.0 y cierre de tareas ODD.

## Log

- L1: "ve una por una resolviendo absolutamente todas las fases con los puntos de mejora que encontraste" — Autorización completa para abordar las 5 fases sistemáticamente.
