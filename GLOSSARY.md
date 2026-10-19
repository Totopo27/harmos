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
El componente del compilador (`core/compiler/ast_extractor.py`) que analiza estáticamente código fuente externo (iniciando por TypeScript) para inferir funciones, clases, tipos de parámetros y valores de retorno, sintetizando automáticamente una Representación Intermedia (`.ir.json`) válida sin intervención manual.

### Meta-Skills del Pipeline
Habilidades operativas especializadas que gobiernan el ciclo de vida de la traducción:
- **`max-transpiler-scout`**: Inspecciona el código externo, audita algoritmos y emite la IR inicial consultando el catálogo canónico.
- **`max-runtime-gatekeeper`**: Audita la compilación CMake, levanta `Max.exe` en bucle cerrado y certifica que la consola interna no reporte errores de ejecución ni desajuste de tipos.

---

## 2. Artefactos de Prueba y Casos Piloto (Downstream Benchmarks)

### Banco de Pruebas (Benchmark / Pilot Case)
Código de aplicación externa seleccionado con el único propósito de someter a estrés y validar las capacidades del Meta-Traductor. **No forma parte de la arquitectura de Harmos ni define su propósito**.
- *Ejemplo piloto*: La suite microtonal de Erv Wilson (`packages/wilson-suite`), el cálculo de inversión n-TET (`tet.circle`) y el modelado físico de mástil (`micro.fretboard`). Son **productos derivados de someter a prueba a Harmos**, nunca el framework en sí.
