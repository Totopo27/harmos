# Feature: SuperCollider Synthesis & Control Pipeline (Fase 4b)
Extracción de grafos de síntesis (SynthDef, UGens), lógica de control (IdentityDictionary, tunings)
y compilación de arquitectura polifónica poly~ para Max MSP.

## Specs

- S1: "Si, adelante con eso" — Autorización para avanzar con la extracción de síntesis de SuperCollider (SCControlExtractor / SCVoiceCompiler).
- S2: Unificar `SCAstExtractor` y `SCControlExtractor` para generar especificaciones IR completas con `data_tables` y `control_interfaces` conformes a `max_object_ir.schema.json`.
- S3: Eliminar omisiones por dependencias de entorno en tests de extracción (`test_sc_control_extractor.py` y `test_real_sc_ingestion.py`), asegurando cobertura del 100% en CI.
- S4: Integrar compilación de sintetizador principal `diesisRosa.maxpat` con `SCVoiceCompiler` recibiendo `control_ir` dinámico y verificando contratos estáticos.
- S5: Validar que la suite completa pase al 100% con 0 tests saltados y certificar con `scripts/check.py`.

## Tasks

- [x] T1 (S2) [inline]: Unificar extracción de DSP (`SCAstExtractor`) y Control (`SCControlExtractor`) con soporte de `object_name`, `data_tables` y `control_interfaces`. Commit: d59f292
- [x] T2 (S3) [inline]: Añadir fixtures embebidos en `tests/test_sc_control_extractor.py` y `tests/test_real_sc_ingestion.py` para ejecución determinista sin `SCMICROSYNTH_ROOT`. Commit: d59f292
- [x] T3 (S4) [inline]: Verificar compilación de `diesisRosa.maxpat` con `control_ir` dinámico en `tests/test_diesis_rosa_main.py`. Commit: d59f292
- [x] T4 (S5) [inline]: Certificar guardrail integral (`scripts/check.py`) con 100% de tests pasando (0 skipped). Commit: d59f292

## Log

- L1: "Si, adelante con eso" — Autorización para avanzar con la extracción de síntesis de SuperCollider.
- L2: Unificada la extracción de AST y Control en `sc_ast_extractor.py`, blindados los tests de SuperCollider con fixtures deterministas (147/147 tests pasando, 0 skipped) y certificado guardrail PASS.
