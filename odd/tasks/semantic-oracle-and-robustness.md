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
- S7: "Quiero que implementes la corrección de F2 + F3 como work unit con su test de reproducibilidad, y luego de esto, quiero que vayas por el pase completo de los LOW"

## Tasks

- [x] T1 (S2) [inline]: Sanear `scripts/audit.py` (sondeo reactivo, lectura binaria `"rb"`, marcador centinela) y tests de auditoría. Commit: 75f9fe3
- [x] T2 (S3) [inline]: Implementar módulo de procedencia `emitted-from.json` y verificación en CLI. Commit: 06bcd03
- [x] T3 (S4) [inline]: Redactar declaración formal de límites del oráculo y honestidad epistémica (I11). Commit: eeda01f
- [x] T4 (S5) [inline]: Implementar veredictos explícitos en benchmarks (I6). Commit: 0eaa05b
- [x] T5 (S6) [inline]: Refactorizar emisión C++ desacoplando Kernel Puro y Binding Min-Devkit. Commit: 70084a0
- [x] T6 (S2) [inline]: Reemplazar aislamiento por centinela/offset por anclaje al header de sesión, parsing estructural de niveles, veredicto fail-closed, resolución de rutas relativas y eliminación de rutas absolutas del código. Commit: cf586ac
- [x] T7 (S7) [inline]: Corregir reproducibilidad del benchmark (F2: muestreo multi-ronda intercalado, medianas, dispersión y lote musical de ratios) y desacoplar vocabulario de auditoría (F3: docs/ORACULO_LIMITES.md, scripts/bench.py, core/compiler/cli.py). Commit: a2bebd5
- [x] T8 (S7) [inline]: Pase completo de hallazgos LOW (F5-F9: inversión core->scripts, min_speedup sin ref, serialización de dispersión, percentil p95 interpolado, CLI unificado, normalización de procedencia) y saneamiento ODD. Commit: 85fe5f5

## Log

- L1: "ok, teniendo esto en cuenta, vamos paso a paso realizando todas las implementaciones que sugieres, cuando tengas una hecha haz commit relacionado a esta, luego procede con la siguiente, así las vamos generando por commits, me parece más ordenado."
- L2: "modifica el informe que hiciste con esto reciente y luego volvamos a retomar el trabajo"
- L3: "Lanza un audit para revisar lo relacionado con esto que hice recién" — Auditoría empírica del verificador en vivo sobre Max 9.1.5 (Windows 10 19045). Defectos confirmados y corregidos: Max trunca `Max.log` en cada arranque, por lo que un `seek` más allá de EOF devolvía 0 líneas y producía `PASS` falso; el centinela se sobrescribía antes de usarse; el glob `*Max 9*/Max.log` nunca coincidía; `"error:"` no matchea el formato real `"error]"`; `"no patcher"` no se detectaba; la primera corrida quedaba `BLOCKED` para siempre; y la heurística de estabilidad (2.5 s) es menor al arranque real (~30 s). Evidencia en vivo: fixture limpio → `PASS` (549 líneas, 0 errores); patcher roto → `FAIL` con `No such object` y `no patcher`. Rutas relativas ahora se resuelven antes de lanzar Max, y `resolve_max_executable` ya no codifica rutas absolutas de host. Suite completa y `scripts/check.py`: PASS.
- L4: "Quiero que implementes la corrección de F2 + F3 como work unit con su test de reproducibilidad, y luego de esto, quiero que vayas por el pase completo de los LOW" — Corrección de F2 (reproducibilidad estadística mediante muestreo multi-ronda, intercalado target/referencia, medianas en speedup y lote musical de ratios de 50 us, logrando desviación típica < 0.05x y 0 flips a NO_SHIP) y F3 (desacople total de 'audit' y 'APROBADO' en cronómetros de Python, disclaimer epistémico anclado a ORACULO_LIMITES.md). Commit: a2bebd5.
- L5: Pase completo de hallazgos LOW (F4-F9): desacople de dependencia core->scripts mediante suites estándar y format_benchmark_report en core.compiler.benchmark (F5, F9b); reporte explícito de min_speedup sin referencia (F6); preservación de speedup 0.0 mediante comprobación is not None (F7); serialización completa de dispersión y medianas en to_dict() (F8); cálculo de p95 con interpolación lineal (F9a); normalización de saltos de línea CRLF->LF en compute_file_sha256 y configuración de .gitattributes (F9c); y sincronización estricta de bookkeeping ODD (F4). Suite completa 100% verde y guardrail PASS.
