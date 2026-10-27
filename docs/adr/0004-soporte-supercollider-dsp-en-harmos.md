# ADR 0004: Extracción de Grafos de Síntesis de SuperCollider y Soporte de DSP en Harmos

- **Estado**: Aceptado
- **Fecha**: 2026-10-26
- **Contexto**: Harmos fue concebido como un meta-traductor universal hacia el ecosistema Cycling '74 Max MSP. Su primera iteración admitía extracción estática de TypeScript para lógica de control e interfaces. Para someter a prueba a Harmos con lenguajes de dominio específico musical (DSL) como SuperCollider (sclang / scsynth) y su ecosistema de `SynthDef`, Harmos necesita entender grafos acíclicos dirigidos (DAG) de generadores unitarios (UGens), distinguiendo señales a tasa de audio (`.ar`) de señales a tasa de control (`.kr`).
- **Decisión**:
  1. **Arquitectura Extensible de Extracción**: Refactorizar la extracción de AST en `core/compiler/ast_extractor.py` introduciendo soporte para detección políglota y un extractor especializado `SCAstExtractor` (o `extract_ir_from_sc_source`).
  2. **Mapeo Formal de Tasa de Cómputo (Audio Rate vs Control Rate)**:
     - Métodos `.ar` (ej. `SinOsc.ar`, `SyncSaw.ar`, `Limiter.ar`, `Out.ar`) se mapean a señales MSP (`~`) con cableado tipado `signal`.
     - Métodos `.kr` / generadores de envolvente (`EnvGen.kr`, `LFTri.kr`) se mapean a objetos de control o generadores de señal de control (`adsr~`, `line~`, `cycle~`).
  3. **Expansión Exhaustiva del Catálogo de Contratos (`max_contracts.json`)**:
     - Agregar los contratos canónicos de objetos matemáticos de audio (`*~`, `+~`, `-~`, `!/~`), osciladores (`phasor~`, `saw~`, `rect~`), envolventes (`adsr~`, `line~`), dinámica (`omx.peaklim~`), e infraestructura de polifonía (`in~`, `out~`, `thispoly~`, `poly~`).
  4. **Patrón de Arquitectura Polifónica para Max**:
     - En lugar de instanciar nodos al vuelo en un único plano (lo cual en Max genera desorden visual y degradación de rendimiento), Harmos sintetizará la voz unitaria en un subpatcher compatible con `poly~`, exponiendo `in~`, `out~` y gestión segura de `thispoly~` para evitar voice leaks.
- **Consecuencias**:
  - **Positivas**: Harmos se vuelve un compilador capaz de procesar no solo código algorítmico imperativo (TS/JS), sino grafos declarativos de DSP de audio procedentes del estándar de facto en síntesis por código (SuperCollider).
  - **Negativas**: Aumenta el catálogo de contratos y la complejidad del motor de validación `ContractEngine`, requiriendo tests exhaustivos por cada nueva familia de objetos MSP.
