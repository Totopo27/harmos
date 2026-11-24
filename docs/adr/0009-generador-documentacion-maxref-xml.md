# ADR 0009: Generador de Documentación Canónica .maxref.xml

- **Estado**: Aceptado
- **Fecha**: 2026-11-23
- **Contexto**: Para que un external u objeto sintetizado por Harmos se integre de forma profesional en Cycling '74 Max, debe proporcionar documentación canónica en el formato XML propietario del visor de Max (`.maxref.xml`). La redacción manual de estos esquemas es redundante y propensa a desincronizarse con los tipos de inlets, outlets y atributos del objeto.
- **Decisión**: Se implementa `core/compiler/maxref_generator.py` como un módulo nuclear del compilador:
  1. Toma la especificación formal del objeto (`.ir.json`) y sintetiza automáticamente un archivo XML `.maxref.xml` válido y canónico.
  2. Mapea metadatos de autoría y categorías, argumentos posicionales (`<objarglist>`), métodos y mensajes derivados de inlets (`<methodlist>`), atributos de inspector con tipado oficial de Max (`<attributelist>`) y sugerencias de objetos relacionados (`<seealsolist>`).
  3. Se integra en el subcomando `harmos compile` (emitiendo tanto en `docs/{object}.maxref.xml` como en la raíz del paquete) y en el subcomando explícito `harmos doc`.
- **Consecuencias**:
  - Positivas: Documentación oficial automática y sincronizada con el código fuente y el esquema IR.
  - Negativas: Requiere mantener actualizadas las descripciones y metadatos en la IR para que el XML contenga texto significativo.
