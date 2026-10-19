# ADR 0003: Extracción Automatizada de AST TypeScript hacia Representación Intermedia (IR)

- **Estado**: Aceptado
- **Fecha**: 2026-10-19
- **Contexto**: Hasta el momento, las especificaciones de Representación Intermedia (`.ir.json`) requerían ser redactadas a mano o guiadas por prompts de meta-skills. Para completar el ciclo de compilación de código externo hacia Max MSP, se necesita un extractor determinista que procese código fuente real.
- **Decisión**: Implementar `core/compiler/ast_extractor.py` priorizando TypeScript/JavaScript:
  1. Utiliza análisis léxico/sintáctico de TypeScript (interfaces, clases, funciones exportadas, tipos de parámetros y tipos de retorno `number`, `string`, `boolean`, `number[]`).
  2. Mapea la función principal o constructor a:
     - Parámetros $\rightarrow$ Inlets de Max (`type: float/int/list/anything`).
     - Valor de retorno $\rightarrow$ Outlet 0 (outlet primario izquierdo).
     - Métodos mutadores secundarios $\rightarrow$ Mensajes de entrada (`messages` en la IR).
  3. Expone la funcionalidad en la CLI de Harmos mediante el subcomando `python -m core.compiler.cli extract <source.ts> --out <spec.ir.json>`.
- **Consecuencias**:
  - Positivas: Cierra el primer tramo del pipeline de Harmos (Código fuente $\rightarrow$ IR automática $\rightarrow$ Parche Maxpat + C++ Min-Devkit).
  - Negativas: Tipos complejos de TypeScript (uniones arbitrarias, tipos genéricos profundos) deben mapearse de forma conservadora al tipo `anything` o descomponerse en listas.
