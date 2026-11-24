# ADR 0013: Lowering Agnóstico de Interfaces UI y Mensajes en Max

- **Estado**: Aceptado
- **Fecha**: 2026-11-24
- **Contexto**: Objetos nativos como `umenu` requieren atributos internos (`items` separados por comas) y las cajas `message` reales en Max contienen el payload en `text` (ej. `"0"` o `"mute 1, 0"`), no el nombre de clase `"message"`. Codificar nombres de escalas o scripts de un proyecto piloto dentro del compilador rompe ADR-0001 y acopla el motor a un dominio específico.
- **Decisión**: Se formaliza un lowering desacoplado de interfaz y mensajes:
  1. `MaxBox` y `TypedPatch` (`core/compiler/typed_patch.py`) soportan `extra_attributes`, `format_umenu_items()` y `add_message()` para poblar atributos GUI nativos y cajas de mensaje con carga literal.
  2. Tanto `TypedPatch._contract_spec()` como `assess_patcher_contracts()` en `scripts/audit.py` mapean cajas con `maxclass == "message"` al contrato `"message"` antes de invocar `ContractEngine`.
  3. `SCVoiceCompiler` y `SCControlExtractor` derivan opciones, tablas y scripts desde `control_ir` con respaldos neutrales (`scale_default.txt`, `pitch_mapper.js`) y cableado íntegro vía `connect_semantic()`.
- **Consecuencias**:
  - Positivas: Parches portables sin artefactos piloto en `core/` y validación exacta de cajas `message` reales.
  - Negativas: Los proyectos piloto deben suministrar su `control_ir` o constantes desde `benchmarks/`.
