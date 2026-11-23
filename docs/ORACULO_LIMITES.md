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

1. **Validez de Contratos Declarados**: **Antes** de arrancar Max, `scripts/audit.py` recorre el contenedor raíz y sus subpatchers con `ContractEngine.assess_connection`. Distingue `VALID`, `INVALID` y `UNVERIFIABLE`. Las conexiones hacia `comment`, los índices negativos o fuera del contrato declarado y las señales hacia entradas exclusivamente de control producen `FAIL`. La ausencia de contratos produce `UNVERIFIABLE`, nunca una aprobación estática. Cuando se emite `PASS`, el detalle declara cuántas conexiones se comprobaron.
2. **Carga Limpia en Tiempo Real**: Una instancia real de `Max.exe` cargó el parche `.maxpat` y la consola interna (`Max.log`) no registró advertencias de tipo (`doesn't match type`), objetos inexistentes (`no such object`) ni violaciones de acceso (`fatal: access violation`).
3. **Procedencia Inmutable**: Si existe `emitted-from.json` junto al patcher, el audit lo verifica **antes** de los contratos y de resolver el runtime, y solo emite `PASS` cuando el veredicto de procedencia es `VALID`: el parche corresponde a la versión de los contratos con la que fue emitido (`core.compiler.provenance`) y los artefactos emitidos (`.maxpat`, `.cpp`, `CMakeLists.txt`) coinciden byte a byte con las huellas SHA-256 registradas. Cualquier otro veredicto (`STALE_CONTRACTS`, `STALE_IR`, `STALE_SOURCE`, `STALE_ARTIFACTS`, `UNVERIFIABLE`, `INVALID`) se emite como veredicto propio del audit con código de salida distinto de cero, sin llegar a validar contratos ni arrancar el paquete en Max. Si no existe huella, el audit no certifica procedencia y el `PASS` lo declara explícitamente en el detalle.

En consecuencia, un parche estructuralmente legal pero emitido contra contratos ya obsoletos **no** obtiene `PASS`: recibe `STALE_CONTRACTS` y debe recompilarse. La procedencia también puede verificarse de forma aislada con `python -m core.compiler.cli verify-provenance <dir>`.

El orden de las puertas es **procedencia → contratos → runtime**. Las dos primeras solo leen archivos: un patcher con cables ilegales recibe `FAIL` incluso sin Max instalado. La evidencia ausente recibe `UNVERIFIABLE`. Si las puertas aplicables aprueban pero falta Max, el resultado es `BLOCKED (RUNTIME_UNAVAILABLE)`; nunca `PASS`.

### Uso estricto y objetos recién generados

- `is_valid_connection()` conserva el resultado `(bool, reason)`; solo `VALID` devuelve `True`.
- Los roles semánticos se resuelven por nombre, alias declarado o coincidencia parcial única del nombre. Un rol desconocido, vacío o ambiguo lanza `IncompatibleConnectionError`; nunca elige el inlet cero por defecto.
- `TypedPatch.connect()` rechaza conexiones no verificables. Un llamador puede usar `allow_unverifiable=True` por conexión; la evaluación queda en `patch.unverifiable_connections` y no se convierte en evidencia válida para el auditor.
- Los tipos pueden declararse como cadena, unión separada por `/` o lista de tipos. La normalización conserva el dato original; el adaptador no desempaqueta una lista si el destino ya la admite.
- El generador usa `ContractEngine.from_ir(ir)` para el objeto nuevo sin modificar el catálogo persistente. Los identificadores de sus puertos deben coincidir con sus posiciones físicas.

Para auditar un paquete generado cuyo objeto no figura en el catálogo:

```bash
python scripts/audit.py --patcher build_harmos/example_test.maxpat --ir example.ir.json
```

`--ir` exige `emitted-from.json` y una huella de IR coincidente antes de usar sus puertos. No permite omitir la auditoría en Max. Un contrato parametrizado no representado debe declararse correctamente antes de conectar; el motor no interpreta argumentos como prueba de puertos adicionales.

---

## 3. Qué NO certifica el veredicto `PASS (ESTRUCTURAL)`

Un veredicto `PASS` **nunca debe interpretarse como prueba de equivalencia algorítmica**. Específicamente, no certifica:

1. **Equivalencia Numérica con el Fuente**: No garantiza que un filtro, escala o función matemática emita los mismos valores flotantes que la librería original en Python, TypeScript o C++.
2. **Identidad de Fase Acústica (Null Test)**: En procesamiento de audio a bloques de 64 muestras (`perform64`), con cuantización de parámetros en el scheduler y optimizaciones de compilador (FMA, AVX), la fase de la señal difiere de modelos en lenguajes de propósito general.
3. **Comportamiento en Rutas de Error no Mapeadas**: No certifica que entradas anómalas (`NaN`, infinitos, cadenas inesperadas) respondan idénticamente al lenguaje origen, salvo que se hayan definido casos de error específicos.
4. **Presupuesto de CPU a 48 kHz**: No certifica que el código no cause sobrecarga de procesamiento en proyectos con alta polifonía (`poly~`).
5. **Cobertura Limitada a Niveles y Patrones Conocidos**: El oráculo solo detecta niveles críticos (`FAIL_LEVELS`: `error`, `fatal`, `critical`) y la lista cerrada de patrones en `FAIL_PATTERNS` (`scripts/audit.py`, ej. `doesn't match type`, `no such object`, `access violation`). Silencios fuera de esa lista no se distinguen de corrección: cualquier advertencia o fallo de Max fuera de esos patrones produce `PASS` sin que ello garantice la ausencia de anomalías.
6. **Completitud de los Contratos**: El auditor no demuestra que la documentación o un contrato registrado describan todo el comportamiento real del objeto. Sí rechaza índices fuera de un contrato conocido y detiene la certificación cuando falta un contrato. Las uniones declaradas no prueban equivalencia semántica ni todas las conversiones posibles de mensajes de Max.
7. **Documentos No Nativos**: Si el `.maxpat` no expone un contenedor `patcher` del formato nativo de Max, la validación de contratos no aplica y el detalle del veredicto lo declara explícitamente (`Contratos no evaluados`). Un `.maxpat` que no sea JSON legible se rechaza con `FAIL` antes de arrancar el runtime.
8. **Conformidad General con JSON Schema**: `scripts/check.py` distingue sintaxis JSON de la estructura soportada del catálogo: entradas/salidas, índices contiguos, nombres, alias y tipos reconocidos. El motor reutiliza esa comprobación al cargar contratos. No es validación general Draft-07 ni conformidad completa del IR con `max_object_ir.schema.json`; no se incorpora `jsonschema` como dependencia. Tampoco ejecuta la auditoría en Max.

---

## 4. Taxonomía de Veredictos del Sistema

| Veredicto | Significado Técnico | Acción del Operador o Agente |
| :--- | :--- | :--- |
| **`PASS`** | Puertas estáticas aplicables aprobadas y sesión real de Max sin errores reconocidos por el auditor. Si el paquete incluye `emitted-from.json`, además la procedencia quedó en `VALID`. No afirma que el auditor haya compilado el paquete. | Proceder a pruebas auditivas manuales dentro del alcance declarado. |
| **`FAIL`** | Patchcord que el contrato declara ilegal, `.maxpat` no legible como documento nativo de Max, error en tiempo de compilación o advertencia en `Max.log`. | Bloqueo estricto. Auto-corrección requerida antes de reintentar. |
| **`BLOCKED`** | Las puertas estáticas (procedencia y contratos) aprobaron, pero `Max.exe` no está instalado en el host, la sesión de log no pudo aislarse o Max no completó la fase de carga. | Prohibido certificar. Se requiere entorno con Cycling '74 Max o investigar la ejecución. |
| **`STALE_CONTRACTS`** | `max_contracts.json` cambió tras la emisión del parche (`verify-provenance`). | Recompilar el parche a partir del IR para actualizar índices y tipos. |
| **`STALE_IR` / `STALE_SOURCE`** | El IR o el código fuente original fueron alterados post-emisión. | Re-ejecutar el pipeline de compilación. |
| **`STALE_ARTIFACTS`** | Un artefacto emitido (`.maxpat`, `.cpp`, `CMakeLists.txt`) difiere de la huella SHA-256 registrada. | Bloqueo estricto. Recompilar y descartar el parche alterado. |
| **`UNVERIFIABLE`** | La evidencia necesaria falta o es inválida: objeto sin contrato, catálogo ilegible o malformado, o evidencia de procedencia insuficiente. | Prohibido certificar. Restituir el contrato o aportar `--ir` con procedencia coincidente para un objeto generado; nunca se degrada a `VALID`. |
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
