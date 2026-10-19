# Harmos

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Max MSP](https://img.shields.io/badge/Cycling_'74-Max_8_%2F_9-purple.svg)](https://cycling74.com/)
[![Target](https://img.shields.io/badge/Target-Max_SDK_%2F_Min--Devkit-orange.svg)](https://github.com/Cycling74/min-devkit)
[![Architecture](https://img.shields.io/badge/Contracts-Zero_Hardcoding-success.svg)](./core/schema/max_contracts.json)
[![Feedback Loop](https://img.shields.io/badge/Live_Audit-0_Console_Errors-brightgreen.svg)](./meta-skills/max-live-verifier/SKILL.md)

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
Ninguna compilación se valida en frío. El motor levanta instancias controladas de `Max.exe`, carga los patchers generados, captura las ventanas y audita los logs de la consola interna de Max. Si aparece una sola advertencia o desajuste de tipos, el pipeline entra en corrección automática antes de dar por cerrada la tarea.

---

## Flujo del pipeline

```
Código fuente externo (C++, Python, JS, Rust)
               │
               ▼
[ 1. max-project-scout ] ──► Audita dependencias, modelos matemáticos y arquitectura
               │
               ▼
[ 2. max-skill-factory ] ──► Genera skills LLM-first ad-hoc para el dominio
               │
               ▼
[ 3. max-catalog-matcher ] ──► Resuelve: Primitiva nativa vs. External C++ nuevo
               │
               ▼
[ 4. Generación IR / C++ ] ──► Genera fuentes Min-Devkit, CMakeLists y patchers
               │
               ▼
[ 5. max-live-verifier ] ──► Levanta Max.exe y audita Max.log (0 errores de consola)
```

---

## Estructura del repositorio

```
harmos/
├── core/
│   └── schema/              # Contratos formales de tipos (max_contracts.json, max_object_ir.json)
├── meta-skills/             # Orquestadores agnósticos del pipeline Harmos
│   ├── max-project-scout/   # Auditoría y extracción de arquitectura previa
│   ├── max-skill-factory/   # Generador de skills bajo el estándar LLM-first
│   ├── max-catalog-matcher/ # Mapeo contra primitivas de Cycling '74
│   ├── max-patch-validator/ # Linteo estricto de inlets, outlets y cables
│   └── max-live-verifier/   # Automatización en vivo y parsing de Max.log
├── skills/                  # Herramientas de soporte y ejemplos generados
│   ├── maxpylang/           # Generación programática reproducible de patchers en Python
│   ├── ersatzben-maxmsp-mcp/# Control e inspección en caliente vía protocolo MCP
│   └── evidence-investigation/ # Protocolo de diagnóstico de código basado en evidencia
├── catalog/                 # Primitivas indexadas y arquetipos de interfaz
├── templates/               # Plantillas base C++ Min-Devkit, CMake y Node for Max
└── benchmarks/              # Suites de prueba y casos piloto para validar el motor
```

> **Nota sobre los benchmarks**: Las suites incluidas en `benchmarks/` y las skills de dominio numérico asociadas corresponden a pruebas de estrés y validación funcional utilizadas durante el desarrollo del framework (ej. cálculo de afinaciones y geometría vectorial). Harmos en sí mismo es el motor agnóstico de traducción, no una librería orientada a un dominio musical particular.

---

## Requisitos de compilación

- **Windows 10 / 11 (x64)**
- **Cycling '74 Max 8.x o Max 9.x** instalado en rutas estándar
- **Visual Studio 2022** con herramientas C++ instaladas (MSVC v143)
- **CMake 3.24+**
- **Git** con soporte para submódulos (para clonar `c74support/min-devkit`)

---

## Licencia

Distribuido bajo licencia [Apache-2.0](./LICENSE).
