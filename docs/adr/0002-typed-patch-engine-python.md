# ADR 0002: Implementación de Harmos Contract Engine en Python con Generación Maxpat Real

- **Estado**: Aceptado
- **Fecha**: 2026-10-19
- **Contexto**: `core/schema/max_contracts.json` contenía contratos pasivos sin ningún motor ejecutable. Existía la inquietud de si una implementación en Python generaría parches funcionales en el formato real de Cycling '74 (`.maxpat`) o solo simulaciones superficiales propensas a fallos en runtime.
- **Decisión**: Implementar `core/compiler/typed_patch.py` en Python con las siguientes garantías:
  1. No es una simulación: Genera directamente la estructura de árbol JSON canónica de Max 8/9 (`patcher`, `boxes`, `lines`, `boxid`, `patching_rect`).
  2. Consulta estricta a `max_contracts.json` antes de emitir cualquier patchline, resolviendo el tipo exacto y el índice físico de inlet/outlet.
  3. Inserción determinista de adaptadores idiomáticos de Max (`unpack`, `flonum`, `route`) cuando se detecta mismatch entre tipos compatibles.
  4. Suite de tests unitarios ejecutables (`tests/test_typed_patch.py`) que comprueba que los parches resultantes cargan limpiamente y respetan la especificación de Max.
- **Consecuencias**:
  - Positivas: Validación instantánea en milisegundos en cualquier entorno sin obligar a compilar binarios C++ para generar un parche. Salida 100% nativa y reproducible.
  - Negativas: Se requiere mantener `max_contracts.json` sincronizado cuando Cycling '74 introduzca nuevos objetos o atributos en versiones futuras de Max.
