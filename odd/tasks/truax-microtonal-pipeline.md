# Feature: Truax Microtonal Kernel & SC Synthesis Pipeline (Fase 4)
Implementación del kernel puro C++17 de Forma Normal de Barry Truax y
soporte diferencial headless en el compilador Harmos.

## Specs

- S1: "Si" — Autorización para avanzar con la síntesis microtonal de Truax / SuperCollider.
- S2: Implementar kernel matemático puro C++17 (`core/compiler/truax_kernel.hpp`) libre de dependencias de Max SDK para cálculo de Forma Normal (`to_normal_form`) y frecuencia carrier (`calc_carrier_freq`).
- S3: Extender `core/compiler/cpp_headless_runner.py` con soporte para `kernel_class="truax"` y validar diferencial contra vectores cosechados (`cases_truax.jsonl`).
- S4: Integrar evaluación diferencial headless en `core/compiler/cli.py` (`harvest` y `diff --suite truax --kernel-class truax`) y tests de CLI.
- S5: Formalizar el contrato canónico de `harmos.truax` en `core/schema/max_contracts.json` y certificar guardrail `scripts/check.py`.

## Tasks

- [x] T1 (S2) [inline]: Implementar `core/compiler/truax_kernel.hpp` con `to_normal_form` y `calc_carrier_freq` en C++17. Commit: 718ded1
- [x] T2 (S3) [inline]: Extender `core/compiler/cpp_headless_runner.py` con `kernel_class="truax"` y tests unitarios. Commit: 718ded1
- [x] T3 (S4) [inline]: Integrar evaluación diferencial C++ headless de Truax en `core/compiler/cli.py` y tests de integración. Commit: 718ded1
- [x] T4 (S5) [inline]: Registrar contrato de `harmos.truax` en `core/schema/max_contracts.json` y certificar guardrail integral. Commit: 718ded1

## Log

- L1: "Si" — Autorización del usuario para arrancar con el pipeline de síntesis microtonal Truax / SuperCollider.
- L2: Implementado kernel C++17 puro `truax_kernel.hpp`, arnés en `cpp_headless_runner.py`, CLI `diff` semántico y contrato canónico `harmos.truax`. Guardrail PASS al 100%.
