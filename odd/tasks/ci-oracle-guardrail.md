# Feature: CI Workflow & Automated Oracle Guardrail (Fase 3)
Automatización continua en GitHub Actions para el oráculo semántico headless,
guardrail de privacidad y contratos, y suite unitaria en CI.

## Specs

- S1: "Pero igual hay que hacer ambas, cierto, así que el orden decidelo tú" — Autorización para ejecutar Fase 3 de infraestructura y CI antes de abordar el hito de interfaz.
- S2: Crear `.github/workflows/ci.yml` activado en `push` y `pull_request` sobre `main` y ramas de características (`feat/*`).
- S3: Configurar matriz de ejecución (`windows-latest`, `ubuntu-latest`) con Python 3.11 y compiladores nativos C++17 (MSVC / GCC).
- S4: Integrar compuertas obligatorias en CI:
  1. `python scripts/check.py` (Unit tests + JSON contracts + PII scan).
  2. Cosecha y diff semántico del oráculo headless C++ (`core.compiler.cli diff` con veredicto `PASS (SEMANTIC)`).
- S5: Actualizar `scripts/check.py` y `tests/test_check.py` para incluir archivos `.yml` y `.yaml` en el escaneo estricto de privacidad.

## Tasks

- [x] T1 (S5) [inline]: Expandir escaneo de privacidad en `scripts/check.py` para archivos YAML (`.yml`, `.yaml`) y añadir test unitario. Commit: 90956d4
- [x] T2 (S2, S3, S4) [inline]: Crear `.github/workflows/ci.yml` con jobs multiplataforma (guardrail, unit tests, diff semántico C++). Commit: b6216b2
- [x] T3 (S4) [inline]: Validar ejecución local de los comandos del workflow y verificar que el guardrail `scripts/check.py` pase al 100%. Commit: b6216b2

## Log

- L1: "Pero igual hay que hacer ambas, cierto, así que el orden decidelo tú" — Inicio de Fase 3: CI & Oráculo Automatizado como base previa a los benchmarks de UI.
- L2: PR #7 creado (https://github.com/Totopo27/harmos/pull/7). Ejecución multiplataforma en GitHub Actions (ubuntu-latest y windows-latest) completada exitosamente con 100% PASS en guardrail, suite unitaria y oráculo headless C++ diferencial.
