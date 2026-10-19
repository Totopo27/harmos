---
name: max-transpiler-scout
description: "Trigger: max-transpiler-scout, auditar repo para max, scout transpiler, generar ir max. Audita código externo, consulta catálogo canónico y emite IR para Max."
license: Apache-2.0
metadata:
  author: "Harmos Core Team"
  version: "1.0.0"
---

# Max Transpiler Scout

## Activation Contract

Cargar cuando se requiera auditar un repositorio o código fuente externo (en cualquier lenguaje: TypeScript/JavaScript, C++, Rust, Python, etc.) con el propósito de portarlo a Max MSP o Max for Live, generando su archivo de Representación Intermedia (`.ir.json`).

## Hard Rules

- **Agnosticismo de Lenguaje Fuente**: Aislar la lógica algorítmica, matemática pura o DSP del código fuente sin importar el lenguaje de origen (`package.json`, `Cargo.toml`, `CMakeLists.txt`, `requirements.txt`).
- **Prioridad de Objeto Nativo (Max SDK First)**:
  - Diseñar la solución prioritariamente como objeto nativo C++ Min-Devkit (`min.object`, `min.dsp`, `ui_operator` con JGraphics) o `jsui` para UI en el patcher.
  - Prohibido recurrir a `jweb` como atajo inicial; solo se admite como excepción justificada si se demuestra inviabilidad técnica en el lienzo de Max.
- **Ley de Cero Reinvención**: Consultar `catalog/max_primitives.json`. Si un requerimiento lo resuelve un objeto estándar (`cycle~`, `makenote`, `dict`, `sprintf`), descartar la creación de externals C++ redundantes.
- **Salida en IR Formal**: El scout debe emitir siempre la especificación estructurada conforme a `core/schema/max_object_ir.schema.json`.

## Decision Gates

| Característica Detectada en Código Origen | Clasificación Arquitectónica Max | Estrategia Canónica |
| :--- | :--- | :--- |
| Audio muestra a muestra, filtros, osciladores | **DSP en tiempo real** | C++ Min-Devkit (`min.dsp`) o `perform64` |
| Matemáticas, tablas de datos, combinatoria | **Control & Lógica** | C++ Min-Devkit (`min.object`) o Max Native |
| Networking, WebSockets, APIs REST, Node | **Red & Transporte** | `node.script` (Node for Max) o `udpsend` |
| UI Vectorial, grillas interactivas, controles | **Max UI Nativo (JGraphics)** | Min-API `ui_operator` o `jsui` (`mgraphics`) |
| UI Web monolítica externa (excepción probada) | **Excepción Híbrida** | Incrustación en `jweb` justificada en IR |

## Execution Steps

1. Inspeccionar arquitectura, dependencias y algoritmos del proyecto fuente.
2. Mapear primitivas nativas reutilizables desde `catalog/max_primitives.json`.
3. Determinar el arquetipo de interfaz (`catalog/archetypes/`) y clasificar la estrategia técnica en la matriz de decisión.
4. Generar el esquema de Representación Intermedia en `benchmarks/<proyecto>/<objeto>_ir.json`.
5. Validar que la IR cumpla con los tipos esperados en `core/schema/max_contracts.json`.

## Output Contract

- Archivo `<objeto>_ir.json` conforme a `max_object_ir.schema.json`.
- Perfil técnico de dependencias y requerimientos de inlets/outlets documentado.

## References

- `core/schema/max_object_ir.schema.json` — Esquema de la representación intermedia.
- `catalog/max_primitives.json` — Catálogo de primitivas de Cycling '74.
