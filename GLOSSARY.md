# Glosario del Dominio Arquitectónico — Harmos

Este documento define la terminología canónica del proyecto Harmos bajo la disciplina de *Domain Modeling*. Queda prohibido mezclar términos del motor central con productos resultantes de sus pruebas.

---

## 1. El Núcleo de Harmos (Framework / Motor)

### Meta-Traductor (Meta-Transpiler)
El motor de compilación, análisis estático y síntesis de software que toma especificaciones de algoritmos en cualquier lenguaje fuente y genera artefactos nativos para el ecosistema de Cycling '74 Max MSP y Max for Live.

### Contrato de Tipos (Type Contract)
Definición formal e inmutable del comportamiento de un objeto en Max (`core/schema/max_contracts.json`). Declara el tipo exacto de cada inlet y outlet (señal MSP `~`, entero, flotante, lista, mensaje de control) para prevenir cables inválidos en tiempo de generación.

### Typed Patcher (`TypedPatch`)
El módulo profundo del compilador que encapsula la construcción de parches `.maxpat`. Valida la compatibilidad de tipos entre salidas y entradas, calcula los índices reales dinámicamente y sintetiza adaptadores transparentes (`unpack`, `flonum`, `route`) antes de escribir el archivo JSON en disco.

### Representación Intermedia (IR — Intermediate Representation)
Esquema formal (`core/schema/max_object_ir.schema.json`) agnóstico del lenguaje que describe la topología, entradas, salidas, atributos y algoritmo de un objeto antes de que Harmos emita código C++ Min-Devkit o scripts.

### Extractor de AST (AST Extractor)
El componente del compilador (`core/compiler/ast_extractor.py`) que analiza estáticamente código fuente externo para inferir funciones, clases, grafos de síntesis (SynthDefs / UGens), tipos de señales y parámetros, sintetizando automáticamente una Representación Intermedia (`.ir.json`) válida sin intervención manual.

### Grafo de Síntesis de Audio (Audio Synthesis Graph)
Estructura formal que representa la topología de un motor sonoro (osciladores, moduladores, generadores de envolvente, filtros y ruteo a buses). Mapea la tasa de cómputo del lenguaje fuente (ej. `.ar` para audio a frecuencia de muestreo y `.kr` para modulación de control) a la infraestructura equivalente de Max/MSP (`~` signals para audio, mensajes o eventos de control para envolventes/parámetros).

### Subpatcher de Voz Polifónica (`poly~` Voice Subpatcher)
Estructura canónica de encapsulación en Max MSP que aloja la instancia unitaria de una voz de síntesis. Define formalmente los puntos de acople mediante objetos `in~`/`in` para señales y mensajes de entrada, `out~`/`out` para bus estéreo/mono de salida, y `thispoly~` para control dinámico de asignación, muting y robo de voces sin fugas de CPU ni cuelgues de notas.

### Grafo de Estado y Control (Control & Table State Graph)
Estructura formal que modela las tablas de datos (afinaciones, buffers, colecciones de armónicos, tablas de consulta) y los mecanismos de selección y conmutación de estado (selectores de escala, enrutadores de presets, parámetros globales). Enlaza de forma declarativa e inmutable las fuentes de datos (`coll`, `buffer~`, `dict`) con los controles de interfaz (`umenu`, `radiogroup`) y los algoritmos matemáticos en tiempo real (`js`, `expr`, `gen~`).

### Meta-Skills del Pipeline
Habilidades operativas especializadas que gobiernan el ciclo de vida de la traducción:
- **`max-transpiler-scout`**: Inspecciona el código externo, audita algoritmos y emite la IR inicial consultando el catálogo canónico.
- **`max-runtime-gatekeeper`**: Audita la compilación CMake, levanta `Max.exe` en bucle cerrado y certifica que la consola interna no reporte errores de ejecución ni desajuste de tipos.

---

## 2. Artefactos de Prueba y Casos Piloto (Downstream Benchmarks)

### Banco de Pruebas (Benchmark / Pilot Case)
Código de aplicación externa seleccionado con el único propósito de someter a estrés y validar las capacidades del Meta-Traductor. **No forma parte de la arquitectura de Harmos ni define su propósito**.
- *Ejemplo piloto*: La suite microtonal de Erv Wilson (`packages/wilson-suite`), el cálculo de inversión n-TET (`tet.circle`) y el modelado físico de mástil (`micro.fretboard`). Son **productos derivados de someter a prueba a Harmos**, nunca el framework en sí.
