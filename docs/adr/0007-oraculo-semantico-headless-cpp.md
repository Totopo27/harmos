# ADR 0007: Oráculo Semántico Headless en C++ Autónomo

- **Estado**: Aceptado
- **Fecha**: 2026-11-23
- **Contexto**: Validar externals y algoritmos de Max MSP únicamente a través del ejecutable interactivo (`Max.exe`) introduce una barrera crítica: en entornos de integración continua (CI, runners de Linux/macOS/Windows sin GUI) Max no está instalado o requiere licencias propietarias, impidiendo validar la corrección matemática de los cálculos.
- **Decisión**: Implementar un oráculo semántico headless en `core/compiler/cpp_headless_runner.py` y `core/compiler/oracle_diff.py`:
  1. Utiliza vectores de prueba deterministas persistidos en formato JSON Lines (`cases.jsonl`).
  2. Detecta el compilador host estándar (`g++`, `clang++`, `cl`) y genera un arnés C++17 autónomo que incluye el header del kernel desacoplado.
  3. Ejecuta los casos en un proceso aislado con control de timeout y captura estructurada de excepciones C++ estándar (`std::exception`).
  4. Compara las salidas producidas contra las expectativas mediante `compare_numeric_or_structure()`, soportando tolerancias combinadas (absoluta y relativa) de punto flotante.
  5. Si ningún compilador C++ está presente en el host, reporta honestamente `BLOCKED (COMPILER_UNAVAILABLE)`, nunca `PASS`.
- **Consecuencias**:
  - Positivas: Pruebas unitarias y de regresión semántica instantáneas en cualquier máquina de desarrollo o runner de CI.
  - Negativas: Requiere mantener sincronizados los vectores de prueba `cases.jsonl` y no sustituye la auditoría de carga en vivo en Max.
