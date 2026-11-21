# Declaración de Límites del Oráculo de Verificación — Harmos

Este documento establece formalmente los límites epistémicos y técnicos del sistema de verificación de Harmos. Inspirado en el principio de honestidad de oráculos (*"What it can't catch"*), delimita con exactitud qué certifica y qué no certifica el veredicto `PASS`.

---

## 1. Filosofía: Legalidad Estructural vs. Equivalencia Semántica

En entornos de flujo de datos y DSP en tiempo real como Cycling '74 Max MSP, el fallo silencioso es la norma: un objeto que calcula incorrectamente una frecuencia o satura una tabla armónica **no genera líneas rojas en la consola de Max**. 

Por ello, la certificación de Harmos se divide formalmente en dos capas:
1. **Oráculo Estructural (`scripts/audit.py`)**: Certifica que el artefacto está correctamente construido, que sus conexiones son válidas y que carga en Max sin errores de runtime.
2. **Oráculo Semántico (`core/compiler/oracle_diff.py`)**: Certifica que el objeto compilado computa los mismos valores que el algoritmo original sobre casos de prueba grabados (`cases.jsonl`) con tolerancia escalar.

---

## 2. Qué certifica el veredicto `PASS (ESTRUCTURAL)`

Cuando `scripts/audit.py` emite un veredicto `PASS`, garantiza de forma verificable:

1. **Validez de Contratos Declarados**: **Antes** de arrancar Max y sin requerir que Max esté instalado, `scripts/audit.py` recorre el `.maxpat` completo (contenedor raíz y subpatchers) y evalúa cada patchline con `ContractEngine.is_valid_connection` (`core/compiler/contract_engine.py`), la misma puerta que usa el emisor al conectar cajas. Se rechaza con `FAIL` cualquier cable que el contrato declare ilegal: conexiones hacia cajas `comment`, y señal de audio (`signal`) hacia un inlet de control (`int`, `float`, `bang`, etc.). Ningún índice de inlet/outlet está codificado en el auditor: el motor los resuelve desde `core/schema/max_contracts.json`. Cuando el `PASS` se emite, el detalle declara cuántas conexiones se validaron.
2. **Carga Limpia en Tiempo Real**: Una instancia real de `Max.exe` cargó el parche `.maxpat` y la consola interna (`Max.log`) no registró advertencias de tipo (`doesn't match type`), objetos inexistentes (`no such object`) ni violaciones de acceso (`fatal: access violation`).
3. **Procedencia Inmutable**: Si existe `emitted-from.json` junto al patcher, el audit lo verifica **antes** de los contratos y de resolver el runtime, y solo emite `PASS` cuando el veredicto de procedencia es `VALID`: el parche corresponde a la versión de los contratos con la que fue emitido (`core.compiler.provenance`) y los artefactos emitidos (`.maxpat`, `.cpp`, `CMakeLists.txt`) coinciden byte a byte con las huellas SHA-256 registradas. Cualquier otro veredicto (`STALE_CONTRACTS`, `STALE_IR`, `STALE_SOURCE`, `STALE_ARTIFACTS`, `UNVERIFIABLE`, `INVALID`) se emite como veredicto propio del audit con código de salida distinto de cero, sin llegar a validar contratos ni arrancar el paquete en Max. Si no existe huella, el audit no certifica procedencia y el `PASS` lo declara explícitamente en el detalle.

En consecuencia, un parche estructuralmente legal pero emitido contra contratos ya obsoletos **no** obtiene `PASS`: recibe `STALE_CONTRACTS` y debe recompilarse. La procedencia también puede verificarse de forma aislada con `python -m core.compiler.cli verify-provenance <dir>`.

El orden de las puertas es **procedencia → contratos → runtime**. Las dos primeras solo leen archivos, por lo que se deciden sin Max instalado: un patcher con cables ilegales recibe `FAIL` también en un host o en un runner de CI sin Cycling '74 Max. `BLOCKED` queda reservado a "todo lo estático aprobó y falta el runtime", de modo que un `BLOCKED` nunca oculta una violación de contratos ya detectable.

---

## 3. Qué NO certifica el veredicto `PASS (ESTRUCTURAL)`

Un veredicto `PASS` **nunca debe interpretarse como prueba de equivalencia algorítmica**. Específicamente, no certifica:

1. **Equivalencia Numérica con el Fuente**: No garantiza que un filtro, escala o función matemática emita los mismos valores flotantes que la librería original en Python, TypeScript o C++.
2. **Identidad de Fase Acústica (Null Test)**: En procesamiento de audio a bloques de 64 muestras (`perform64`), con cuantización de parámetros en el scheduler y optimizaciones de compilador (FMA, AVX), la fase de la señal difiere de modelos en lenguajes de propósito general.
3. **Comportamiento en Rutas de Error no Mapeadas**: No certifica que entradas anómalas (`NaN`, infinitos, cadenas inesperadas) respondan idénticamente al lenguaje origen, salvo que se hayan definido casos de error específicos.
4. **Presupuesto de CPU a 48 kHz**: No certifica que el código no cause sobrecarga de procesamiento en proyectos con alta polifonía (`poly~`).
5. **Cobertura Limitada a Niveles y Patrones Conocidos**: El oráculo solo detecta niveles críticos (`FAIL_LEVELS`: `error`, `fatal`, `critical`) y la lista cerrada de patrones en `FAIL_PATTERNS` (`scripts/audit.py`, ej. `doesn't match type`, `no such object`, `access violation`). Silencios fuera de esa lista no se distinguen de corrección: cualquier advertencia o fallo de Max fuera de esos patrones produce `PASS` sin que ello garantice la ausencia de anomalías.
6. **Objetos sin Contrato y Rangos No Ejercidos**: La validación de patchcords solo aplica una regla cuando ambos extremos declaran contrato en `max_contracts.json`. Un objeto ausente del esquema se evalúa de forma permisiva (sin contrato no hay regla que violar), y un índice de inlet/outlet fuera del rango declarado tampoco se rechaza, porque `ContractEngine` lo permite explícitamente por el dinamismo de Max. Esos casos solo se detectan si Max los reporta durante la carga.
7. **Documentos No Nativos**: Si el `.maxpat` no expone un contenedor `patcher` del formato nativo de Max, la validación de contratos no aplica y el detalle del veredicto lo declara explícitamente (`Contratos no evaluados`). Un `.maxpat` que no sea JSON legible se rechaza con `FAIL` antes de arrancar el runtime.
8. **Conformidad del IR con el Esquema**: Ningún componente valida el `.ir.json` contra `core/schema/max_object_ir.schema.json`. `scripts/check.py` solo comprueba que cada archivo de `core/schema/` sea JSON parseable; el proyecto no usa un validador de esquema (`jsonschema` no es dependencia). Un IR malformado se detecta, como mucho, por los errores que produzca al compilar o al cargar el patcher.

---

## 4. Taxonomía de Veredictos del Sistema

| Veredicto | Significado Técnico | Acción del Operador o Agente |
| :--- | :--- | :--- |
| **`PASS`** | Patchcords validados contra `max_contracts.json` antes de arrancar Max, compilación exitosa y cero líneas rojas en `Max.log`. Si el paquete incluye `emitted-from.json`, además la procedencia quedó en `VALID`. | Proceder a empaquetado o pruebas auditivas manuales. |
| **`FAIL`** | Patchcord que el contrato declara ilegal, `.maxpat` no legible como documento nativo de Max, error en tiempo de compilación o advertencia en `Max.log`. | Bloqueo estricto. Auto-corrección requerida antes de reintentar. |
| **`BLOCKED`** | Las puertas estáticas (procedencia y contratos) aprobaron, pero `Max.exe` no está instalado en el host, la sesión de log no pudo aislarse o Max no completó la fase de carga. | Prohibido certificar. Se requiere entorno con Cycling '74 Max o investigar la ejecución. |
| **`STALE_CONTRACTS`** | `max_contracts.json` cambió tras la emisión del parche (`verify-provenance`). | Recompilar el parche a partir del IR para actualizar índices y tipos. |
| **`STALE_IR` / `STALE_SOURCE`** | El IR o el código fuente original fueron alterados post-emisión. | Re-ejecutar el pipeline de compilación. |
| **`STALE_ARTIFACTS`** | Un artefacto emitido (`.maxpat`, `.cpp`, `CMakeLists.txt`) difiere de la huella SHA-256 registrada. | Bloqueo estricto. Recompilar y descartar el parche alterado. |
| **`UNVERIFIABLE`** | La evidencia necesaria no existe o no puede leerse (contratos ilegibles, artefacto registrado ausente, huella no registrada). | Prohibido certificar. Restituir la evidencia y re-verificar; nunca se degrada a `VALID`. |
| **`INVALID`** | `emitted-from.json` no existe, no es JSON parseable, o su estructura es malformada (raíz o secciones que no son objetos). | Prohibido certificar. Regenerar el paquete. |

### Veredictos del Oráculo Semántico (`diff`)

El comando `python -m core.compiler.cli diff` evalúa la equivalencia funcional de cálculo contra casos grabados (`cases.jsonl`) y emite:
- **`PASS (SEMANTICO)`**: El kernel computa los mismos valores que el oráculo sobre `cases.jsonl` dentro de la tolerancia numérica declarada.
- **`FAIL (MISMATCH)`**: Discrepancia numérica superior a la tolerancia o ruta de error divergente al evaluar `cases.jsonl`.

### Evaluación de Rendimiento en Python (`bench`) vs. Oráculo de Verificación

Los comandos `python scripts/bench.py` y `python -m core.compiler.cli bench` evalúan presupuestos de latencia en microsegundos dentro del intérprete Python host (`time.perf_counter_ns`) y emiten veredictos de decisión:

- **`SHIP`**: La rutina evaluada se mantiene estrictamente dentro de los presupuestos de latencia (`max_latency_us`, `max_p95_latency_us`) y aceleración (`min_speedup`).
- **`NO_SHIP`**: La rutina excede el presupuesto de tiempo real o presenta una desaceleración inaceptable.

> **Distinción Epistémica Estricta**:  
> `SHIP` y `NO_SHIP` son métricas de simulación en Python host. **Bajo ninguna circunstancia sustituyen o constituyen un veredicto `PASS` de auditoría**, el cual queda reservado exclusivamente a la ejecución en vivo dentro de Cycling '74 Max (`scripts/audit.py`). Los términos `audit`, `PASS` y `APROBADO` no deben ser empleados para describir benchmarks de Python.

---

## 5. Regla para Agentes y Desarrolladores

> **Prohibido asumir corrección matemática por ausencia de errores de consola.**  
> Todo reporte de entrega de parches o externals debe citar este documento y explicitar el alcance de la verificación realizada.
