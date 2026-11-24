# Orden de las puertas estáticas del oráculo

Objetivo: que las puertas estáticas de `scripts/audit.py` (procedencia y contratos) se evalúen antes de resolver el runtime, para que un host sin Max distinga un patcher ilegal (`FAIL`) de un runtime ausente (`BLOCKED`).
Rama: `fix/audit-static-gates-order` · Entrega: un work-unit commit · Runner: `python -m unittest discover tests`

## Specs

**S1.** En un host sin Max, un `.maxpat` con un cable que el contrato declara ilegal devuelve `FAIL` con el detalle `Contratos rechazados` (hoy devuelve `BLOCKED`).

**S2.** En un host sin Max, un `.maxpat` cuyo contenido no es JSON legible devuelve `FAIL` con el mensaje `no es un documento JSON nativo de Max` (hoy devuelve `BLOCKED`).

**S3.** En un host sin Max, un patcher sin violaciones sigue devolviendo `BLOCKED` con `Max.exe no fue detectado` y la instrucción de instalar Max o definir `MAX_PATH`. `BLOCKED` pasa a significar "todo lo estático pasó, falta el runtime".

**S4.** La procedencia precede a los contratos: un paquete cuyo `emitted-from.json` está obsoleto conserva su veredicto propio (`STALE_CONTRACTS`, `STALE_IR`, `STALE_SOURCE`, `STALE_ARTIFACTS`, `UNVERIFIABLE`, `INVALID`) aunque sus cables fueran ilegales bajo el esquema vigente. Motivo: no se juzga un patcher contra un esquema para el que no fue emitido.

**S5.** Ni `Max.exe` ni `subprocess.Popen` se invocan cuando una puerta estática rechaza.

**S6.** `docs/ORACULO_LIMITES.md` declara que `BLOCKED` implica puertas estáticas aprobadas y que la validación de contratos no requiere Max instalado.

## Tasks

| ID | Specs | Ruta | Estado |
| :--- | :--- | :--- | :--- |
| T1 | S1-S4 | inline | [x] RED: tests que fallan contra el orden actual |
| T2 | S1-S5 | inline | [x] GREEN: reorden en `audit_patcher_live` |
| T3 | S6 | inline | [x] docs |
| T4 | S1-S6 | inline | [x] verificación: suite, `check.py`, e2e sin y con Max |

## Log

**L1 (petición original, verbatim):** "¿Abro `fix/audit-static-gates-order` con su doc y su RED primero?" — respuesta: "adelante con eso"

**L2 (diagnóstico):** la puerta de contratos quedó detrás de `resolve_max_executable()` (`scripts/audit.py:468`), así que en un host sin Max devuelve `BLOCKED` y `scripts/check.py` nunca la ejerce. Una comprobación estática no debe depender de que exista el runtime.

**L3 (decisión de orden):** procedencia antes que contratos. Si `emitted-from.json` ya declara deriva de contratos, validar los cables contra el esquema actual produce violaciones que no son responsabilidad del operador: el veredicto correcto es el de procedencia.
