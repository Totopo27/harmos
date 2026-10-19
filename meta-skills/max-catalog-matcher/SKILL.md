---
name: max-catalog-matcher
description: "Trigger: max-catalog-matcher, mapear objetos max, zero reinvention. Mapea requerimientos al catálogo de Max y define estrategia C++ nativa vs híbrida."
license: Apache-2.0
metadata:
  author: "OptimizandoParaMaxSDK"
  version: "2.1"
---

# Max Catalog Matcher

## Activation Contract

Cargar tras completar el scouting de un proyecto para mapear requerimientos técnicos contra primitivas de Max MSP y determinar la estrategia de implementación óptima.

## Hard Rules

- **Cero Reinvención**: Consultar obligatoriamente `catalog/max_primitives.json`. Si un requerimiento lo cubre un objeto estándar de Max (`cycle~`, `makenote`, `dict`), prohibido crear un external C++ innecesario.
- **Prioridad de Objeto Nativo (Max SDK First)**: Diseñar elementos interactivos prioritariamente como objetos nativos en el lienzo (`ui_operator` con JGraphics o `jsui`). El uso de `jweb` solo se admite como excepción técnica justificada.
- **Mandato de Tipado Estricto**: Todo enlace entre objetos debe satisfacer las especificaciones de `core/schema/max_contracts.json`.
- **Inspección de Lienzo con Servidores MCP**: Usar herramientas MCP (`MaxMCP` o `ersatzben-maxmsp-mcp`) para consultar geometría del canvas y evitar colisiones (`get_avoid_rect_position`).

## Decision Gates

| Requerimiento Técnico | Disponibilidad en Catálogo | Estrategia de Implementación |
| :--- | :--- | :--- |
| Funcionalidad resuelta por primitiva | Sí (`cycle~`, `makenote`, `sprintf`) | Reutilizar objeto nativo existente |
| Control interactivo en canvas | No | C++ Min-Devkit (`ui_operator`) o `jsui` |
| DSP personalizado o matemática pura | No | C++ Min-Devkit (`min.dsp` o `min.object`) |
| UI Web compleja no reproducible en canvas | Inviabilidad nativa probada | Excepción documentada con `jweb` |

## Execution Steps

1. Leer requerimientos técnicos del reporte de `max-project-scout`.
2. Mapear primitivas nativas consultando `catalog/max_primitives.json`.
3. Diseñar la implementación como objeto nativo Max SDK (Min-Devkit o `jsui`).
4. Si la natividad resulta inviable de forma demostrable, evaluar excepción con `jweb`.
5. Estructurar la Representación Intermedia (IR) en `benchmarks/<proyecto>/<objeto>_ir.json`.
6. Validar que la solución admita verificación comparativa 1:1 contra el código fuente.

## Output Contract

- Archivo IR JSON o especificación de parche con contratos de inlets/outlets.
- Selección justificada de estrategia nativa vs excepción híbrida.

## References

- `references/matcher-guidelines.md` — Consulta del catálogo de primitivas, jerarquía nativa y esquemas IR.
