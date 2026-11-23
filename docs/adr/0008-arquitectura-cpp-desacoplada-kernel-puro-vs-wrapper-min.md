# ADR 0008: Arquitectura C++ Desacoplada: Kernel Puro vs. Wrapper Min-Devkit

- **Estado**: Aceptado
- **Fecha**: 2026-11-23
- **Contexto**: Incrustar la lógica algorítmica y las estructuras de cálculo dentro de las clases de Min-Devkit (`c74::min::object`, macros `MIN_DESCRIPTION`, tipos `c74::min::sample`) crea un acoplamiento rígido con el SDK de Max. Esto imposibilita compilar, perfilar y testear los algoritmos con herramientas estándar de C++ fuera de la infraestructura pesada de Cycling '74.
- **Decisión**: Se adopta el patrón de dos capas desacopladas para todo código C++ generado por Harmos (`core/compiler/cpp_generator.py`):
  1. **Kernel C++ Puro (`{object}_kernel.hpp`)**: Contiene únicamente la clase de procesamiento (`harmos::kernels::{Object}Kernel`), métodos puros (`process_scalar`, `process_sample`, `process_block`) y estado algorítmico, con cero dependencias de cabeceras de Max SDK.
  2. **Wrapper Min-Devkit (`{object}.cpp`)**: Capa delgada de integración que instancia el kernel como miembro, expone los inlets/outlets y atributos de Inspector oficiales de Max, y mapea los eventos de entrada al kernel.
- **Consecuencias**:
  - Positivas: El kernel puede ser evaluado por el oráculo semántico headless en milisegundos con cualquier compilador C++17 (`g++`, `clang++`, `cl`). Los algoritmos pueden reutilizarse en otros targets (VST, AU, CLI).
  - Negativas: Se generan dos archivos fuente en lugar de uno por cada external de C++.
