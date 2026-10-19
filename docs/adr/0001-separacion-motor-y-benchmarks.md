# ADR 0001: Separación Estricta entre el Motor Harmos y los Bancos de Prueba

- **Estado**: Aceptado
- **Fecha**: 2026-10-19
- **Contexto**: Durante las primeras fases de desarrollo se utilizó una suite microtonal de afinaciones de Erv Wilson y geometría n-TET para estresar y validar el generador de código C++ Min-Devkit y los parches de Max. Esto provocó ambigüedad sobre si Harmos era un proyecto musical/microtonal o un compilador de software.
- **Decisión**: Se establece una frontera arquitectónica irrevocable:
  1. **Harmos** es única y exclusivamente el motor de compilación agnóstico, el motor de contratos ejecutables (`TypedPatch`), los esquemas IR y las meta-skills del pipeline.
  2. Todo código matemático de afinaciones, objetos `wilson.*`, `tet.*` o `micro.*` residen en carpetas de prueba (`benchmarks/` y `packages/`) como **artefactos downstream generados por Harmos**, sin contaminar la identidad, el README ni las dependencias troncales del framework.
- **Consecuencias**:
  - Positivas: El framework mantiene su alcance general aplicable a cualquier dominio de software (física, DSP, redes, visuales).
  - Negativas: Se requiere mantener una distinción explícita en la documentación para no confundir a futuros colaboradores.
