# ADR 0005: Representación Intermedia de Control, Tablas de Datos y Conmutación en Harmos

## Estado
Aceptado

## Contexto
Durante el benchmark de síntesis con el proyecto `diesisRosa` (SCMicroSynth), Harmos demostró una capacidad sobresaliente para extraer y sintetizar el grafo de audio (UGens en cascada de FM a objetos `cycle~`, `adsr~`, `poly~` con 0 errores en Live Runtime Audit). Sin embargo, se identificó una brecha arquitectónica crítica:
SuperCollider divide los sistemas de síntesis en dos capas:
1. **Capa DSP (Servidor `scsynth`)**: `SynthDef` compuesto por UGens de señal `.ar` y control `.kr`.
2. **Capa de Control y Estado (Intérprete `sclang`)**: Estructuras de datos (`IdentityDictionary`, colecciones, generadores de afinaciones microtonales en `tunings.scd`, gestión de presets y conmutadores de modo).

El extractor previo (`SCAstExtractor`) solo procesaba `SynthDef`, omitiendo la estructura declarativa de control. Como consecuencia, el compilador generó un parche atado a una escala estática (31-TET) en lugar de exponer el catálogo completo de 10 afinaciones conmutables que el código fuente ya poseía.

## Decisión
1. **Extensión del Esquema IR (`max_object_ir.schema.json`)**:
   Incorporar campos formales de nivel superior:
   - `data_tables`: Arreglos y diccionarios de datos a persistir como artefactos de consulta (`coll`, `buffer~`, `dict`).
   - `control_interfaces`: Selectores dinámicos de estado (`umenu`, `radiogroup`, `tab`) y su ruteo hacia las tablas.
   - `math_kernels`: Scripts externos (`js`, `gen~`) requeridos para transformaciones dinámicas.

2. **Extractor de Control y Estado (`SCControlExtractor`)**:
   Implementar un analizador estático para `sclang` que:
   - Detecte diccionarios de afinaciones y métodos generadores (`build31TET`, `build41TET`, etc.).
   - Emita la especificación de tablas de consulta y conecte automáticamente selectores (`umenu` -> `prepend read` -> `coll`) sin intervención manual ni asunciones en código suelto.

3. **Cero Hardcoding e Integridad de Pipeline**:
   Toda conexión entre el selector de control y los componentes de audio debe ser validada contra `max_contracts.json` vía `TypedPatch`.

## Consecuencias
- **Positivas**:
  - Harmos se convierte en un compilador de sistemas completos (Audio + Control + Datos) y no solo de voces aisladas.
  - Se elimina el riesgo de que proyectos microtonales o basados en presets queden congelados en un estado estático por omisión del programador.
  - Se preserva la fidelidad semántica 1:1 entre el programa fuente y el parche generado de Max MSP.
- **Negativas / Desafíos**:
  - Mayor complejidad en el análisis estático de SCLang para interpretar colecciones y llamadas a métodos generadores.
