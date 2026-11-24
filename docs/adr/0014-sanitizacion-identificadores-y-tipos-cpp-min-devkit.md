# ADR 0014: Sanitización de Identificadores y Tipado C++ para Min-DevKit

- **Estado**: Aceptado
- **Fecha**: 2026-11-24
- **Contexto**: Los nombres de objetos y atributos declarados en `.ir.json` pueden contener puntos (ej. `harmos.demo`), guiones, dígitos iniciales o palabras reservadas de C++ (`default`, `class`). Además, los kernels DSP con múltiples puertos de señal requieren aridad exacta en `sample_operator<N_IN, N_OUT>` y los atributos no numéricos (`symbol`, `bool`) fallan al mapearse como `double`.
- **Decisión**: `core/compiler/cpp_generator.py` aplica sanitización y tipado estricto:
  1. `cpp_identifier()` normaliza nombres a identificadores C++17 válidos (`_IDENTIFIER_UNSAFE`, prefijo `_` ante dígitos y sufijo `_` frente a `_CPP_KEYWORDS`), conservando el nombre original en metadatos públicos de Max.
  2. `generate_min_wrapper()` computa dinámicamente `sample_operator<N_IN, N_OUT>` desde `_is_signal_port()` y emite `attribute<symbol>` / `attribute<bool>` con `_cpp_string_literal()` y `_cpp_bool_literal()`.
- **Consecuencias**:
  - Positivas: Cabeceras y wrappers compilables sin errores sintácticos con `g++ -fsyntax-only`, `clang++` o MSVC `cl`.
  - Negativas: Exige que todo nuevo tipo de atributo añadido al esquema IR tenga mapeo explícito en el generador C++.
