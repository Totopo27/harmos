# Flujo de Trabajo: Construcción del Meta-Traductor para Max MSP

> **Metodología**: Project Architect con Compuertas de Validación Binarias (*Decision Gates*), Receipt-Driven Development (RDD) y Skills Modulares.

---

## 1. Mandato Fundamental: CERO HARDCODING A NIVEL GENERAL

Para toda fase actual y futura de este proyecto:
- **Prohibición de valores mágicos y lógica estática**: Queda prohibido cablear índices fijos a ciegas, dejar constantes numéricas no parametrizables, fijar frecuencias o escalas rígidas en C++, o quemar IPs/puertos sin exposición de atributos.
- **Parametrización Dinámica Total**:
  1. Todo comportamiento debe exponerse como atributo nativo en el **Inspector de Max**.
  2. Todo atributo debe ser modificable en caliente mediante mensajes por los inlets.
  3. Toda conexión entre objetos debe resolverse dinámicamente consultando los esquemas formales de contrato (`core/schema/max_contracts.json`).
  4. Los objetos deben ser agnósticos y adaptables a cualquier proyecto externo entrante.

---

## 2. Matriz de Roles y Skills Especializadas

| Skill | Responsabilidad | Entrada | Salida |
| :--- | :--- | :--- | :--- |
| **`project-architect`** | Coordinación de arquitectura, diseño de compuertas y gobierno del sistema. | Requerimientos de usuario | Planes, gates y validaciones |
| **`max-project-scout`** | Análisis del proyecto de origen, auditoría de dependencias y recopilación de documentación de dominio. | Repositorio / Código fuente externo | `recursos_<proyecto>.md` y perfil técnico |
| **`max-skill-factory`** | Generación dinámica de skills de dominio en `.opencode/skills/` basadas en `skill-creator`. | Perfil técnico y necesidades de dominio | Skills locales ad-hoc con frontmatter LLM-first |
| **`max-catalog-matcher`**| Comparación contra el catálogo canónico de Max. Detecta objetos nativos a reutilizar o arquetipos a extender (ej. `kslider`). | Lista de requerimientos del proyecto | Matriz de reuso vs. nuevos objetos y esquemas IR |
| **`max-sdk-generator`** | Generación de código fuente (C++ min-devkit, Node for Max, JGraphics, CMakeLists). | Esquemas IR y plantillas de Max | Código C++, CMake y metadatos de Max |
| **`max-patch-validator`**| Validación de tipado e interconexiones de inlets/outlets según las restricciones canónicas de Max. | Patcher `.maxpat` y advertencias | Patcher corregido sin errores de tipo |
| **`max-live-verifier`** | Ejecución de `Max.exe` en vivo, captura visual del patcher y auditoría de la Max Console. Feedback loop autónomo hasta 0 errores. | External compilado y patch de prueba | Captura visual y confirmación binaria de consola limpia |

---

## 2. Fases de Desarrollo con Compuertas Binarias (Gates)

```
[Fase 0: Cimientos Arquitectónicos] 
       │ 
       ▼ (Gate 0: Documentación y estructura de carpetas sellada)
[Fase 1: Catálogo Canónico de Max & Arquetipos] 
       │ 
       ▼ (Gate 1: Base de datos de objetos nativos y arquetipo kslider modelado)
[Fase 2: Motor Meta-Skill Factory & Scout] 
       │ 
       ▼ (Gate 2: Scout y Factory generan skills funcionales para un repo de prueba)
[Fase 3: Motor de Representación Intermedia (IR) y Plantillas C++] 
       │ 
       ▼ (Gate 3: Generación de objeto C++ funcional a partir de un esquema IR)
[Fase 4: Benchmark 1 — Caso Piloto Módulo Wilson] 
       │ 
       ▼ (Gate 4: Objeto wilson.core compila a .mxe64 y calcula ratios exactamente igual que en JS)
[Fase 5: Benchmark 2 — wilson.hexslider (Variante Arquetipo kslider)] 
       │ 
       ▼ (Gate 5: Objeto UI interactúa en Max con mouse y emite listas de pitch/velocity microtonal)
[Fase 6: Benchmark 3 y 4 — Diapason y MidiControl] 
       │ 
       ▼ (Gate 6: Suite completa de paquetes integrada con MPE/MIDI y visualizador)
```

---

### Fase 0: Cimientos Arquitectónicos y Estructura del Entorno
- **Objetivo**: Establecer la arquitectura del traductor, el gobierno de hilos de Max y estructurar el repositorio.
- **Actividades**:
  1. Redactar `ARQUITECTURA_TRADUCTOR_MAX.md`.
  2. Redactar `FLUJO_DE_TRABAJO.md` con compuertas binarias.
  3. Crear estructura de carpetas: `core/`, `meta-skills/`, `templates/`, `catalog/`, `benchmarks/`.
- **Compuerta de Salida (Gate 0)**:
  - `ARQUITECTURA_TRADUCTOR_MAX.md` y `FLUJO_DE_TRABAJO.md` aprobados.
  - Estructura de directorios creada en el disco.
  - Criterio binario: `test-path` positivo para todos los directorios base.

---

### Fase 1: Catálogo Canónico de Max y Arquetipos Estándar
- **Objetivo**: Crear la base de conocimiento para que el traductor jamás reinvente objetos nativos y sepa adaptar arquetipos como `kslider`.
- **Actividades**:
  1. Crear `catalog/max_primitives.json`: Listado de objetos nativos de Max para matemáticas, audio, MIDI, OSC, buffers y listas con sus especificaciones de inlets/outlets.
  2. Crear `catalog/archetypes/kslider.md`: Desglose formal del comportamiento del `kslider` (mouse down, note-on, note-off, drag, visual feedback, atributos de inspector) como base para teclados microtonales.
- **Compuerta de Salida (Gate 1)**:
  - Archivo `max_primitives.json` validado con al menos 40 objetos nativos esenciales de Max.
  - Especificación formal de `kslider` completa y lista para ser usada por el generador.

---

### Fase 2: Motor Meta-Skill Factory & Scout
- **Objetivo**: Crear las skills del sistema capaces de auditar cualquier repositorio externo y generar dinámicamente skills de dominio especializadas.
- **Actividades**:
  1. Crear la skill `max-project-scout`.
  2. Crear la skill `max-skill-factory` (basada en el estándar de `skill-creator`).
  3. Prueba de concepto: Ejecutar el scout sobre `Teclados-Wilson` y verificar la generación de una skill ad-hoc (ej. `wilson-tuning-auditor`).
- **Compuerta de Salida (Gate 2)**:
  - Ejecutar scout sobre un módulo y comprobar que la skill generada en `.opencode/skills/` es válida según el estándar YAML y LLM-first.

---

### Fase 3: Motor de Representación Intermedia (IR) y Plantillas C++
- **Objetivo**: Formalizar el esquema de IR para objetos de Max y tener las plantillas base listas para compilar con CMake.
- **Actividades**:
  1. Definir el esquema JSON-Schema / YAML para el IR (`core/schema/max_object_ir.schema.json`).
  2. Configurar plantillas C++ probadas en `templates/`:
     - `min_object_control`: Objeto estándar para cálculo de control.
     - `min_object_dsp`: Objeto con `perform64` para audio.
     - `node_script_wrapper`: Wrapper para Node for Max.
- **Compuerta de Salida (Gate 3)**:
  - Compilación exitosa de prueba con CMake/MSVC de la plantilla `min_object_control` produciendo un binario `.mxe64` válido.

---

### Fase 4: Benchmark 1 — Caso Piloto Módulo Wilson (Afinación)
- **Objetivo**: Traducir el primer módulo real aislado: el cálculo matemático de afinaciones de `Teclados-Wilson` a un objeto nativo de Max (`wilson.cps` o `wilson.ratios`).
- **Actividades**:
  1. Ejecutar el Scout sobre `Teclados-Wilson` (extrayendo las matrices de ratios y combinatoria de factores primos).
  2. Mapear y generar el objeto C++ usando `min-devkit`.
  3. Compilar `.mxe64`.
- **Compuerta de Salida (Gate 4)**:
  - Prueba de exactitud: Las frecuencias y ratios calculados por el external en Max coinciden al 100% (error < 0.0001 Hz) con los resultados de `hexany-data.js` de Wilson.

---

### Fase 5: Benchmark 2 — El Teclado Hexagonal (`wilson.hexslider`)
- **Objetivo**: Resolver la variante especializada inspirada en `kslider` para teclados hexagonales microtonales.
- **Actividades**:
  1. Usar el arquetipo de `kslider` y la geometría hexagonal de Wilson (`hexgrid.js`).
  2. Diseñar e implementar el objeto de interfaz `wilson.hexslider` (vía JGraphics C++ o JS Painter para Max).
  3. Probar la emisión de eventos de clic/hover y salida de pitch microtonal/velocity.
- **Compuerta de Salida (Gate 5)**:
  - El objeto se inserta en un patch de Max, dibuja la retícula hexagonal, responde a interacción del ratón y emite eventos de nota idénticos en convención al `kslider` pero con microtonalidad.

---

### Fase 6: Benchmarks 3 y 4 — Diapasón y MidiControl
- **Objetivo**: Completar la integración de visualización de mástil (`Diapason-microtonal`) y el bridge de control/MPE (`midiControl`), reutilizando los objetos nativos de red y MIDI de Max.
- **Compuerta de Salida (Gate 6)**:
  - Patch integral de Max donde un teclado Wilson o un diapasón controla un sintetizador MPE y envía/recibe OSC utilizando los objetos nativos de Max más los nuevos externals generados por el traductor.
