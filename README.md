# Harmos

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Max MSP](https://img.shields.io/badge/Cycling_'74-Max_8_%2F_9-purple.svg)](https://cycling74.com/)
[![Target](https://img.shields.io/badge/Target-Max_SDK_%2F_Min--Devkit-orange.svg)](https://github.com/Cycling74/min-devkit)


Meta-traductor y generador de ecosistemas para Cycling '74 Max MSP y Max for Live.

Harmos es un framework agnóstico de compilación y orquestación. Su función es tomar código fuente, librerías o algoritmos desarrollados en cualquier lenguaje (C++, Python, Rust, TypeScript) y transmutarlos de forma reproducible al modelo nativo de Max: objetos atómicos (`.mxe64`), módulos DSP de baja latencia (`min.dsp`), controles vectoriales interactivos (`ui_operator`, `jsui`) y patchers estructurados (`.maxpat`, `.amxd`).

---

## El problema con portar código a Max

Quien intenta llevar una librería o un algoritmo externo al entorno de Max suele tropezar con dos problemas estructurales:

1. **El parche monolítico inmanejable**: Intentar meter miles de líneas de lógica en un script suelto de Node o JavaScript, generando bloqueos en el hilo principal y cuellos de botella gráficos.
2. **El cableado a ciegas**: Escribir generadores que asumen de memoria qué inlet recibe un valor o qué outlet emite una señal. Al primer cambio en el patcher, los cables se cruzan, la consola se llena de texto rojo y el motor DSP falla en silencio.

Harmos descarta el empirismo y aborda la portabilidad como un problema formal de ingeniería de compiladores y teoría de contratos.

---

## Principios de diseño

### 1. Cero hardcoding (Dynamic Contract Matching)
Ninguna conexión se traza adivinando índices de inlets o outlets. Todo objeto o external registra su firma estricta en [`core/schema/max_contracts.json`](./core/schema/max_contracts.json). Si un módulo envía un canal MIDI hacia `midiformat`, Harmos consulta el esquema para resolver que el destino exacto es el inlet 6. Si el contrato no valida, el parche no se emite.

### 2. Descomposición atómica
No se trasladan bibliotecas enteras a una única caja negra. Se dividen las responsabilidades:
- **Cálculo y control**: Objetos C++ en el hilo de control o scheduler (`min.object`).
- **DSP en tiempo real**: Procesamiento muestra a muestra en la interrupción de audio (`perform64` / `min.dsp`), sin asignaciones dinámicas de memoria (`malloc`) ni llamadas bloqueantes al sistema operativo.
- **Visualización interactiva**: Lienzo nativo con JGraphics o `jsui` (`mgraphics`), desacoplado del procesamiento de señal.

### 3. Reuso del catálogo canónico
Si Max ya cuenta con primitivas probadas (`mtof`, `dict`, `coll`, `udpreceive`), Harmos no fabrica externals redundantes: construye abstracciones de conexión alrededor del estándar. Si existe un arquetipo interactivo consagrado (como `kslider`), toma su contrato como base para derivar variantes especializadas según los requerimientos del dominio origen.

### 4. Bucle cerrado de verificación en vivo (RDD)
Ninguna compilación se valida en frío. El motor levanta instancias controladas de `Max.exe`, carga los patchers generados, captura las ventanas y audita los logs de la consola interna de Max. Si aparece una sola advertencia o desajuste de tipos, el pipeline entra en corrección automática antes de dar por cerrada la tarea. Todo veredicto delimita explícitamente su alcance técnico conforme a [`docs/ORACULO_LIMITES.md`](./docs/ORACULO_LIMITES.md).

---

## Flujo del pipeline

```
Código fuente externo (C++, Python, JS/TS, SuperCollider)
               │
               ▼
[ 1. max-transpiler-scout / extract ] ──► Auditoría estática y extracción de IR (.ir.json)
               │                          consultando catalog/ y max_contracts.json
               ▼
[ 2. core.compiler.cli compile ]      ──► Validación tri-estado (ContractEngine, TypedPatch)
               │                          y síntesis de kernel puro (*_kernel.hpp), wrapper Min (*.cpp),
               │                          CMakeLists.txt, .maxpat, .maxref.xml y emitted-from.json
               ▼
[ 3. Oráculo semántico headless ]     ──► Verificación diferencial C++ (harvest / diff) sobre
               │                          cases.jsonl sin requerir runtime propietario
               ▼
[ 4. max-runtime-gatekeeper / audit ] ──► Compuertas procedencia → contratos → runtime en vivo
                                          sobre Max.exe / Max (Max.log, 0 errores)
```

---

## Uso del CLI y scripts canónicos

Todos los subcomandos del compilador se ejecutan vía `python -m core.compiler.cli`:

```bash
# 1. Compilar una IR a paquete Max completo (modo por defecto o explícito con "compile")
python -m core.compiler.cli benchmarks/midiControl/micro_mpe_ir.json --out build_e2e/micro_mpe_pkg --no-build
python -m core.compiler.cli compile <archivo.ir.json> --out ./build_harmos --source <src>

# 2. Extraer una especificación IR desde TypeScript o JavaScript
python -m core.compiler.cli extract <fuente.ts> --out <salida.ir.json> --name <harmos.objeto>

# 3. Generar documentación canónica .maxref.xml desde una IR
python -m core.compiler.cli doc <archivo.ir.json> --out docs/ --author "Harmos Meta-Compiler"

# 4. Verificar la huella criptográfica de procedencia (emitted-from.json)
python -m core.compiler.cli verify-provenance <dir_paquete> --ir <archivo.ir.json> --source <src>

# 5. Cosechar vectores de prueba semánticos hacia cases.jsonl
python -m core.compiler.cli harvest --suite wilson --out cases_wilson.jsonl --tolerance 1e-7

# 6. Ejecutar oráculo diferencial semántico (Python o kernel C++ headless)
python -m core.compiler.cli diff cases_wilson.jsonl --suite wilson
python -m core.compiler.cli diff cases_wilson.jsonl --cpp-kernel benchmarks/teclados-wilson/wilson_kernel.hpp --kernel-class wilson

# 7. Evaluar presupuestos de rendimiento en Python host (SHIP / NO_SHIP)
python -m core.compiler.cli bench --suite all
```

Scripts canónicos de verificación:

```bash
# Guardrail pre-commit completo (tests unitarios + contratos + escaneo de privacidad)
python scripts/check.py

# Auditoría estructural y en vivo en Cycling '74 Max (procedencia → contratos → runtime)
python scripts/audit.py --patcher <ruta/al/parche.maxpat> --ir <archivo.ir.json>

# Benchmark de presupuestos de rendimiento en JSON
python scripts/bench.py --suite all --json
```

---

## Estructura del repositorio

```
harmos/
├── core/
│   ├── compiler/            # Motor determinista: CLI, TypedPatch, ContractEngine, extractores AST/SC, generadores C++ y Maxref
│   └── schema/              # Contratos de tipos (max_contracts.json) y esquema IR (max_object_ir.schema.json)
├── meta-skills/             # Habilidades agnósticas del pipeline Harmos
│   ├── max-transpiler-scout/# Auditoría estática y extracción políglota hacia IR
│   └── max-runtime-gatekeeper/ # Verificación en vivo en Max y oráculo semántico
├── catalog/                 # Primitivas indexadas y arquetipos de interfaz (max_primitives.json)
├── templates/               # Plantillas base C++ Min-Devkit, Node for Max y MaxPyLang
├── scripts/                 # Verificadores canónicos (check.py, audit.py, bench.py)
├── tests/                   # Suite unitaria, contratos, oráculos y paridad documental
├── docs/                    # ADRs (docs/adr/), guías de agentes (docs/agents/) y ORACULO_LIMITES.md
├── benchmarks/              # Suites de estrés y casos piloto para validar el motor
├── packages/                # Paquetes Max de referencia generados para validación (ej. wilson-suite/)
├── skills/                  # Skills de dominio y herramientas auxiliares del ecosistema
├── odd/                     # Seguimiento de entregas bajo Organic Driven Development (odd/tasks/)
├── pyproject.toml           # Metadatos Python, grupo dev (ruff, coverage) y reglas de linting
├── GLOSSARY.md              # Terminología canónica del dominio arquitectónico
├── CONTRIBUTING.md          # Guía de contribución, invariantes y flujo ODD
└── AGENTS.md                # Reglas operativas para agentes de código
```

> **Nota sobre los benchmarks**: Las suites incluidas en `benchmarks/`, `packages/` y las skills de dominio asociadas corresponden a pruebas de estrés y validación funcional utilizadas durante el desarrollo del framework (ej. cálculo de afinaciones y geometría vectorial). Harmos en sí mismo es el motor agnóstico de traducción, no una librería orientada a un dominio musical particular (véase [`docs/adr/0001-separacion-motor-y-benchmarks.md`](./docs/adr/0001-separacion-motor-y-benchmarks.md)).

---

## Requisitos de desarrollo y compilación

- **Python 3.11+** (Windows, macOS o Linux para suite de tests, validación de contratos y oráculo headless C++)
- **Dependencias de desarrollo**: `python -m pip install --group dev` (`ruff`, `coverage`; véase [`pyproject.toml`](./pyproject.toml))
- **Compilador C++17** (`g++`, `clang++` o MSVC `cl`) para ejecutar pruebas del arnés headless (`cpp_headless_runner.py`)
- **Cycling '74 Max 8.x o Max 9.x** instalado en rutas estándar (obligatorio para auditorías en vivo vía `scripts/audit.py`)
- **CMake 3.24+** y submódulo `c74support/min-devkit` (para compilar externals nativos `.mxe64` / `.mxo`)

Consulta [`CONTRIBUTING.md`](./CONTRIBUTING.md) para el flujo completo de contribución y checklist pre-commit.

---

## Licencia

Distribuido bajo licencia [Apache-2.0](./LICENSE).
