---
name: max-project-scout
description: "Trigger: max-project-scout, auditar proyecto max, analizar repo externo. Audita código externo y genera perfil técnico para traducción nativa a Max MSP."
license: Apache-2.0
metadata:
  author: "OptimizandoParaMaxSDK"
  version: "2.1"
---

# Max Project Scout

## Activation Contract

Cargar al auditar código fuente externo (TypeScript/JavaScript, C++, Rust, Python, C#, WebAssembly) para portarlo o traducirlo a objetos, patchers o librerías de Cycling '74 Max MSP o Max for Live.

## Hard Rules

- **Agnosticismo de Lenguaje**: Extraer arquitectura, modelos y algoritmos sin importar el stack de origen (`package.json`, `Cargo.toml`, `CMakeLists.txt`, `requirements.txt`).
- **Prohibido Reduccionismo Ciego**: Mapear todas las capacidades interactivas y herramientas del original sin reducirlas forzosamente a objetos elementales de Max.
- **Aislamiento Estricto de Lógica vs Presentación**: Separar DSP, afinaciones y matemática pura de la capa de renderizado visual.
- **Prioridad Absoluta de Objeto Nativo (Max SDK First)**: Diseñar prioritariamente la solución como objeto nativo en el lienzo (`min.object`, `min.dsp`, `ui_operator` con JGraphics o `jsui`). El uso de `jweb` es un último recurso excepcional admisible únicamente tras probar inviabilidad nativa en Max.
- **Protocolo de Paridad Funcional**: Diseñar un método de contraste empírico 1:1 entre el proyecto original y el objeto de Max.

## Decision Gates

| Característica en Código Fuente | Clasificación Arquitectónica | Estrategia Mandatoria en Max |
| :--- | :--- | :--- |
| Audio muestra a muestra, síntesis, filtros | DSP en tiempo real | C++ Min-Devkit (`min.dsp`), `gen~` |
| Afinaciones, matemática pura, combinatoria | Control & Math | C++ Min-Devkit (`min.object`), MaxPyLang |
| WebSockets, APIs REST, scripts de red | Red & Transporte | `node.script` (Node for Max), `udpsend` |
| UI Vectorial, grillas, dials, arcos Bézier | Max UI Nativo (PRIORIDAD) | Min-API `ui_operator` (JGraphics) o `jsui` |
| UI Web compleja no integrable en lienzo | Excepción Híbrida | `jweb` (solo con inviabilidad nativa probada) |

## Execution Steps

1. Inspeccionar arquitectura, dependencias y algoritmos del repositorio original.
2. Identificar y aislar módulos matemáticos y de procesamiento de audio.
3. Evaluar viabilidad de interfaz mapeando controles a primitivas de Max SDK o JGraphics.
4. Definir la estrategia de traducción (Ruta Nativa SDK vs Excepción documentada).
5. Diseñar el plan de pruebas de paridad funcional paso a paso.
6. Generar el reporte técnico de arquitectura en `benchmarks/<proyecto>/ANALISIS_ARQUITECTURA_<proyecto>.md`.

## Output Contract

- Documento `ANALISIS_ARQUITECTURA_<proyecto>.md` con:
  - Stack y algoritmos aislados.
  - Especificación del objeto nativo Max SDK.
  - Justificación de estrategia de UI y plan de paridad funcional.

## References

- `references/scout-methodology.md` — Metodología de análisis agnóstico de lenguaje, jerarquía nativa y pruebas de paridad.
