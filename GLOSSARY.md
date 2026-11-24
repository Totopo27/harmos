# Glosario del Dominio Arquitectónico — Harmos

Este documento define la terminología canónica del proyecto Harmos bajo la disciplina de *Domain Modeling*. Queda prohibido mezclar términos del motor central con productos resultantes de sus pruebas.

---

## 1. El Núcleo de Harmos (Framework / Motor)

### Meta-Traductor (Meta-Transpiler)
El motor de compilación, análisis estático y síntesis de software que toma especificaciones de algoritmos en cualquier lenguaje fuente y genera artefactos nativos para el ecosistema de Cycling '74 Max MSP y Max for Live.

### Contrato de Tipos (Type Contract)
Definición formal e inmutable del comportamiento de un objeto en Max (`core/schema/max_contracts.json`). Declara el tipo exacto de cada inlet y outlet (señal MSP `~`, entero, flotante, lista, mensaje de control) para prevenir cables inválidos en tiempo de generación.

### Typed Patcher (`TypedPatch`)
El módulo profundo del compilador que encapsula la construcción de parches `.maxpat`. Valida la compatibilidad de tipos entre salidas y entradas, calcula los índices reales dinámicamente y sintetiza adaptadores transparentes (`unpack`, `flonum`, `route`) antes de escribir el archivo JSON en disco.

### Representación Intermedia (IR — Intermediate Representation)
Esquema formal (`core/schema/max_object_ir.schema.json`) agnóstico del lenguaje que describe la topología, entradas, salidas, atributos y algoritmo de un objeto antes de que Harmos emita código C++ Min-Devkit o scripts.

### Extractor de AST (AST Extractor)
El componente del compilador (`core/compiler/ast_extractor.py`, `sc_ast_extractor.py`) que analiza estáticamente código fuente externo para inferir funciones, clases, grafos de síntesis (SynthDefs / UGens), tipos de señales y parámetros, sintetizando automáticamente una Representación Intermedia (`.ir.json`) válida sin intervención manual.

### Grafo de Síntesis de Audio (Audio Synthesis Graph)
Estructura formal que representa la topología de un motor sonoro (osciladores, moduladores, generadores de envolvente, filtros y ruteo a buses). Mapea la tasa de cómputo del lenguaje fuente (ej. `.ar` para audio a frecuencia de muestreo y `.kr` para modulación de control) a la infraestructura equivalente de Max/MSP (`~` signals para audio, mensajes o eventos de control para envolventes/parámetros).

### Subpatcher de Voz Polifónica (`poly~` Voice Subpatcher)
Estructura canónica de encapsulación en Max MSP que aloja la instancia unitaria de una voz de síntesis. Define formalmente los puntos de acople mediante objetos `in~`/`in` para señales y mensajes de entrada, `out~`/`out` para bus estéreo/mono de salida, y `thispoly~` para control dinámico de asignación, muting y robo de voces sin fugas de CPU ni cuelgues de notas.

### Grafo de Estado y Control (Control & Table State Graph)
Estructura formal que modela las tablas de datos (afinaciones, buffers, colecciones de armónicos, tablas de consulta) y los mecanismos de selección y conmutación de estado (selectores de escala, enrutadores de presets, parámetros globales). Enlaza de forma declarativa e inmutable las fuentes de datos (`coll`, `buffer~`, `dict`) con los controles de interfaz (`umenu`, `radiogroup`) y los algoritmos matemáticos en tiempo real (`js`, `expr`, `gen~`).

### Huella de Procedencia (Provenance Record / `emitted-from.json`)
Registro criptográfico inmutable con firmas SHA-256 de los contratos canónicos de Max, especificaciones IR, código fuente original y artefactos generados. Garantiza detección determinista de deriva y reproducibilidad matemática del pipeline.

### Oráculo Semántico Headless (`cases.jsonl` + `cpp_headless_runner.py`)
Mecanismo de verificación diferencial y matemática que contrasta salidas de kernels C++ autónomos contra vectores de prueba esperados bajo tolerancias escalares de coma flotante, sin requerir entorno gráfico ni runtime propietario.

### Oráculo Estructural en Vivo (`scripts/audit.py`)
Verificador dinámico en bucle cerrado que ejecuta instancias reales de `Max.exe` / `Max`, inyecta patchers generados y audita la bitácora interna (`Max.log`) para certificar ausencia de cables cruzados, fallos de tipado o errores de instanciación en tiempo de ejecución.

### Guardrail (`scripts/check.py`)
Compuerta estática y dinámica pre-commit fail-closed que ejecuta el 100% de los tests unitarios, audita la integridad estructural de los esquemas JSON y escanea el árbol en busca de secretos, PII y rutas absolutas de host.

### Generador Maxref (`.maxref.xml` / `maxref_generator.py`)
Sintetizador de documentación canónica oficial de Cycling '74 Max. Genera los metadatos XML que alimentan el visor de ayuda y el inspector nativo a partir de las entradas, salidas y atributos del IR.

### Kernel C++ Desacoplado (Decoupled Pure Kernel)
Patrón de diseño arquitectónico que separa el algoritmo matemático y de procesamiento de señal (`*_kernel.hpp`, 0 dependencias externas) del wrapper delgado de Min-Devkit (`*.cpp`), permitiendo testing headless en CI y reutilización en otros entornos.

### Lowering de UI (`control_interfaces` / `extra_attributes`)
Transformación de especificaciones declarativas de interacción visual (ej. menús desplegables, selectores de escala, botones) a atributos y estructuras nativas de Max (`umenu`, `radiogroup`, `gain~`).

### Organic Driven Development (ODD)
Metodología de desarrollo guiada por trazabilidad estricta y compuertas binarias, donde cada evolución del sistema se registra mediante especificaciones (`S#`), tareas (`T#`), bitácora (`L#`) y commits atómicos con verificación probada.

### Taxonomía de Veredictos del Sistema (System Verdict Taxonomy)
Conjunto canónico y exhaustivo de estados binarios de evaluación:
- **`PASS (ESTRUCTURAL)`**: Patcher verificado en vivo en Max con 0 errores de consola en `Max.log`.
- **`PASS (SEMANTIC)`**: Kernel verificado contra vectores de prueba `cases.jsonl` dentro de la tolerancia numérica.
- **`BLOCKED (RUNTIME_UNAVAILABLE)`**: Runtime de Max ausente en el host; auditoría en vivo bloqueada de forma honesta.
- **`BLOCKED (COMPILER_UNAVAILABLE)`**: Compilador C++ (g++, clang++, cl) ausente en el host; arnés headless bloqueado.
- **`STALE_CONTRACTS`**: Los contratos canónicos de Max han cambiado desde la emisión del paquete.
- **`STALE_IR` / `STALE_SOURCE`**: La IR o el código fuente original fueron modificados tras la generación.
- **`STALE_ARTIFACTS`**: Uno o más artefactos emitidos fueron alterados manualmente tras la emisión.
- **`UNVERIFIABLE`**: La evidencia requerida para la certificación no está disponible en el entorno.
- **`INVALID`**: Registro o archivo malformado que no cumple la estructura mínima esperada.
- **`FAIL`**: Discrepancia numérica, excepción no controlada o error de compilación.

### Evaluación Tri-Estado de Contratos (Tri-State Assessment)
Mecanismo estricto de validación implementado en `ContractEngine.assess_connection()` (`core/compiler/contract_engine.py`, ADR-0010) que evalúa cada conexión candidata devolviendo un `ConnectionAssessment` con uno de tres estados explícitos: **`VALID`** (puertos presentes y compatibles según la matriz señal/control), **`INVALID`** (violación contractual detectable estáticamente, p. ej. señal hacia inlet exclusivamente de control, conexión hacia `comment` o índice fuera de rango) y **`UNVERIFIABLE`** (contrato ausente para alguno de los objetos). Un objeto sin contrato nunca se aprueba en silencio (`is_valid_connection()` solo devuelve `True` para `VALID`, y `validate_connection()` rechaza `INVALID` y `UNVERIFIABLE` salvo `allow_unverifiable=True`).

### Aridad Dinámica (Dynamic Arity)
Síntesis en tiempo de compilación del esquema de inlets y outlets mediante `ContractEngine._synthesize_dynamic_contract()` para objetos nativos de Max cuya topología de puertos depende de sus argumentos de instanciación (`unpack`, `pack`, `trigger` / `t`, `route`). Evita el hardcoding de índices al derivar tipos, roles semánticos y número exacto de puertos directamente desde los argumentos declarados en la caja.

### Veredictos de Presupuesto de Rendimiento (SHIP / NO_SHIP)
Veredicto categórico emitido por `core/compiler/benchmark.py` (`scripts/bench.py` y `python -m core.compiler.cli bench`) tras evaluar las latencias medidas en el intérprete Python host contra un `PerformanceBudget` (`max_latency_us`, `max_p95_latency_us`, `min_speedup` con `tolerance_margin`). **`SHIP`** indica cumplimiento estricto de todos los umbrales configurados; **`NO_SHIP`** indica exceso de latencia, regresión de aceleración o ausencia de muestras de referencia/medición. Conforme a [`docs/ORACULO_LIMITES.md`](./docs/ORACULO_LIMITES.md), `SHIP` mide rendimiento en Python host y **nunca sustituye** al veredicto `PASS` de una auditoría en vivo en Cycling '74 Max (`scripts/audit.py`).

### Meta-Skills del Pipeline
Habilidades operativas especializadas que gobiernan el ciclo de vida de la traducción:
- **`max-transpiler-scout`**: Inspecciona el código externo, audita algoritmos y emite la IR inicial consultando el catálogo canónico.
- **`max-runtime-gatekeeper`**: Audita la compilación CMake, levanta `Max.exe` en bucle cerrado y certifica que la consola interna no reporte errores de ejecución ni desajuste de tipos.

---

## 2. Artefactos de Prueba y Casos Piloto (Downstream Benchmarks)

### Banco de Pruebas (Benchmark / Pilot Case)
Código de aplicación externa seleccionado con el único propósito de someter a estrés y validar las capacidades del Meta-Traductor. **No forma parte de la arquitectura de Harmos ni define su propósito**.
- *Ejemplo piloto*: La suite microtonal de Erv Wilson (`benchmarks/teclados-wilson`), la síntesis FM por Forma Normal de Barry Truax (`diesisRosa`), el cálculo de inversión n-TET (`tet.circle`) y el modelado físico de mástil (`micro.fretboard`). Son **productos derivados de someter a prueba a Harmos**, nunca el framework en sí.
