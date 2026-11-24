# ADR 0011: Orden y Prioridad de Compuertas: Verificación Estática Previa a la Auditoría en Vivo

- **Estado**: Aceptado
- **Fecha**: 2026-11-23
- **Contexto**: Ejecutar auditorías en vivo levantando `Max.exe` (`scripts/audit.py`) es un proceso pesado: requiere inicializar la interfaz gráfica, el motor de audio y el subsistema de drivers, además de depender de la presencia física de la aplicación en el host. Enviar patchers con errores sintácticos, discrepancias matemáticas o contratos rotos a la auditoría en vivo introduce latencia innecesaria y riesgo de procesos huérfanos.
- **Decisión**: Se establece una jerarquía determinista de compuertas ordenadas por costo computacional y rapidez de feedback (*Fail-Fast Pipeline*):
  1. **Compuerta 1 (Estática - Microsegundos)**: Validación estructural de tipos y contratos en memoria mediante `ContractEngine` y `TypedPatch`.
  2. **Compuerta 2 (Estática - Milisegundos)**: Huella criptográfica SHA-256 de procedencia (`emitted-from.json`) para certificar ausencia de deriva.
  3. **Compuerta 3 (Semántica Headless - Segundos)**: Compilación del arnés C++ autónomo y evaluación contra vectores de prueba `cases.jsonl` mediante `cpp_headless_runner.py`.
  4. **Compuerta 4 (Pre-Commit Guardrail - Segundos)**: Ejecución de `scripts/check.py` (suite de tests unitarios, esquemas JSON y escaneo de privacidad/PII).
  5. **Compuerta 5 (Auditoría en Vivo - Runtime)**: Invocación de `scripts/audit.py` con `Max.exe` únicamente si las 4 compuertas anteriores resultaron en `PASS`. Si el ejecutable de Max no está disponible, el estado es `BLOCKED (RUNTIME_UNAVAILABLE)`, sin provocar un fallo ficticio de la suite estática.
- **Consecuencias**:
  - Positivas: Detección instantánea de errores en las capas más rápidas; consumo óptimo de recursos en desarrollo local y CI.
  - Negativas: Los desarrolladores deben familiarizarse con el orden de diagnóstico y resolver primero los fallos estáticos antes de auditar en vivo.
