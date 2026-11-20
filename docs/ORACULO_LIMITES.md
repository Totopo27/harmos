# Declaración de Límites del Oráculo de Verificación — Harmos

Este documento establece formalmente los límites epistémicos y técnicos del sistema de verificación de Harmos. Inspirado en el principio de honestidad de oráculos (*"What it can't catch"*), delimita con exactitud qué certifica y qué no certifica el veredicto `PASS`.

---

## 1. Filosofía: Legalidad Estructural vs. Equivalencia Semántica

En entornos de flujo de datos y DSP en tiempo real como Cycling '74 Max MSP, el fallo silencioso es la norma: un objeto que calcula incorrectamente una frecuencia o satura una tabla armónica **no genera líneas rojas en la consola de Max**. 

Por ello, la certificación de Harmos se divide formalmente en dos capas:
1. **Oráculo Estructural (En producción hoy)**: Certifica que el artefacto está correctamente construido, que sus conexiones son válidas y que carga en Max sin errores de runtime.
2. **Oráculo Semántico (Fase 2 del roadmap)**: Certifica que el objeto compilado computa los mismos valores que el algoritmo original sobre casos de prueba grabados (`cases.jsonl`).

---

## 2. Qué certifica el veredicto `PASS (ESTRUCTURAL)`

Cuando `scripts/audit.py` emite un veredicto `PASS`, garantiza de forma verificable:

1. **Validez Estricta de Contratos**: Todos los patchcords cumplen con los tipos de inlets y outlets definidos en `core/schema/max_contracts.json`. No existen cables a etiquetas `comment` ni índices erróneos en objetos sensibles (ej. `midiformat`).
2. **Conformidad de Esquema**: La Representación Intermedia (`.ir.json`) cumple al 100% con `core/schema/max_object_ir.schema.json`.
3. **Carga Limpia en Tiempo Real**: Una instancia real de `Max.exe` cargó el parche `.maxpat` y la consola interna (`Max.log`) no registró advertencias de tipo (`doesn't match type`), objetos inexistentes (`no such object`) ni violaciones de acceso (`fatal: access violation`).
4. **Procedencia Inmutable**: Si existe `emitted-from.json`, el parche corresponde exactamente a la versión de los contratos con la que fue emitido (`core.compiler.provenance`), y los artefactos emitidos (`.maxpat`, `.cpp`, `CMakeLists.txt`) coinciden byte a byte con las huellas SHA-256 registradas. Si la evidencia no puede leerse, el veredicto es `UNVERIFIABLE` y nunca `VALID`. Un registro sin huella de artefactos (formato previo) certifica solo los insumos y lo declara explícitamente en el detalle.

---

## 3. Qué NO certifica el veredicto `PASS (ESTRUCTURAL)`

Un veredicto `PASS` **nunca debe interpretarse como prueba de equivalencia algorítmica**. Específicamente, no certifica:

1. **Equivalencia Numérica con el Fuente**: No garantiza que un filtro, escala o función matemática emita los mismos valores flotantes que la librería original en Python, TypeScript o C++.
2. **Identidad de Fase Acústica (Null Test)**: En procesamiento de audio a bloques de 64 muestras (`perform64`), con cuantización de parámetros en el scheduler y optimizaciones de compilador (FMA, AVX), la fase de la señal difiere de modelos en lenguajes de propósito general.
3. **Comportamiento en Rutas de Error no Mapeadas**: No certifica que entradas anómalas (`NaN`, infinitos, cadenas inesperadas) respondan idénticamente al lenguaje origen, salvo que se hayan definido casos de error específicos.
4. **Presupuesto de CPU a 48 kHz**: No certifica que el código no cause sobrecarga de procesamiento en proyectos con alta polifonía (`poly~`).

---

## 4. Taxonomía de Veredictos del Sistema

| Veredicto | Significado Técnico | Acción del Operador o Agente |
| :--- | :--- | :--- |
| **`PASS`** | Patcher estructuralmente legal, compilación exitosa y cero líneas rojas en `Max.log`. | Proceder a empaquetado o pruebas auditivas manuales. |
| **`FAIL`** | Error en tiempo de compilación, patchcord incompatible o advertencia en `Max.log`. | Bloqueo estricto. Auto-corrección requerida antes de reintentar. |
| **`BLOCKED (RUNTIME_UNAVAILABLE)`** | `Max.exe` no está instalado o no se detectó en el host. | Prohibido certificar. Se requiere entorno con Cycling '74 Max. |
| **`STALE_CONTRACTS`** | `max_contracts.json` cambió tras la emisión del parche (`verify-provenance`). | Recompilar el parche a partir del IR para actualizar índices y tipos. |
| **`STALE_IR` / `STALE_SOURCE`** | El IR o el código fuente original fueron alterados post-emisión. | Re-ejecutar el pipeline de compilación. |
| **`STALE_ARTIFACTS`** | Un artefacto emitido (`.maxpat`, `.cpp`, `CMakeLists.txt`) difiere de la huella SHA-256 registrada. | Bloqueo estricto. Recompilar y descartar el parche alterado. |
| **`UNVERIFIABLE`** | La evidencia necesaria no existe o no puede leerse (contratos ilegibles, artefacto registrado ausente, huella no registrada). | Prohibido certificar. Restituir la evidencia y re-verificar; nunca se degrada a `VALID`. |
| **`INVALID`** | `emitted-from.json` no existe o no es JSON parseable. | Prohibido certificar. Regenerar el paquete. |

---

## 5. Regla para Agentes y Desarrolladores

> **Prohibido asumir corrección matemática por ausencia de errores de consola.**  
> Todo reporte de entrega de parches o externals debe citar este documento y explicitar el alcance de la verificación realizada.
