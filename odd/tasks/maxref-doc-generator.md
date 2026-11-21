# Feature: Maxref Documentation Generator (Fase 6)
Generador automático de documentación canónica .maxref.xml para Cycling '74 Max
a partir de especificaciones de Representación Intermedia (IR).

## Specs

- S1: "está bien, vamos con eso" — Autorización para implementar la síntesis automática de `.maxref.xml`.
- S2: Implementar `core/compiler/maxref_generator.py` para sintetizar el documento XML conforme a la especificación oficial de Max (`c74object`, `digest`, `description`, `metadatalist`, `methodlist`, `attributelist`, `seealsolist`).
- S3: Integrar la generación de `.maxref.xml` en `core/compiler/cli.py` dentro de `compile_ir` y como subcomando independiente `harmos doc <ir_file> --out <dir>`.
- S4: Añadir pruebas unitarias completas en `tests/test_maxref_generator.py` y actualizar `tests/test_cli.py`.
- S5: Validar que todos los tests pasen al 100% y certificar con `scripts/check.py`.

## Tasks

- [x] T1 (S2) [inline]: Implementar `core/compiler/maxref_generator.py` con mapeo canónico de tipos, métodos y atributos a XML. Commit: e801174
- [x] T2 (S3) [inline]: Integrar `generate_maxref` en `core/compiler/cli.py` (`compile_ir` y subcomando `doc`). Commit: e801174
- [x] T3 (S4) [inline]: Crear suite de pruebas unitarias en `tests/test_maxref_generator.py` e integración en `tests/test_cli.py`. Commit: e801174
- [x] T4 (S5) [inline]: Certificar guardrail integral (`scripts/check.py`). Commit: e801174

## Log

- L1: "está bien, vamos con eso" — Inicio de la implementación del generador de documentación Maxref.
- L2: Implementado `core/compiler/maxref_generator.py` con soporte completo de metadatos, objargs, métodos por inlet y mensajes, atributos y seealso por categoría.
- L3: Integrado en `core/compiler/cli.py` (`compile_ir` emite `docs/<object>.maxref.xml` y lo registra en `emitted-from.json`; nuevo subcomando `harmos doc`).
- L4: Suites de pruebas en `tests/test_maxref_generator.py` y `tests/test_cli.py` pasando al 100% (152/152 tests globales).
- L5: Guardrail `scripts/check.py` PASS.
