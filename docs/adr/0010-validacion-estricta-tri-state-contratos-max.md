# ADR 0010: Validación Estricta Tri-State de Contratos de Conexión en Max MSP

- **Estado**: Aceptado
- **Fecha**: 2026-11-23
- **Contexto**: El runtime de Max MSP opera bajo dos regímenes temporales disjuntos: el hilo de control (mensajes asíncronos y eventos de scheduler) y el hilo DSP (interrupción periódica de audio a frecuencia de muestreo). Trazar cables entre puertos incompatibles (ej. conectar un mensaje de control a una entrada puramente de señal o viceversa sin convertidores como `sig~` o `snapshot~`) corrompe el comportamiento del patcher.
- **Decisión**: Se implementa en `ContractEngine` (`core/compiler/contract_engine.py`) un validador de conexiones de tres estados (*Tri-State Assessment*):
  1. **Compatible (`True`)**: Tipos de salida y entrada formalmente compatibles bajo la matriz de reglas (control a control, señal a señal, o inlets híbridos que admiten unión `signal/float` o `float/signal`).
  2. **Incompatible (`False`)**: Violación de contrato detectable estáticamente (ej. señal conectada a un inlet de control exclusivo o mensaje a inlet de señal exclusiva). Lanza `IncompatibleConnectionError` e impide emitir el patcher.
  3. **No Verificable (`None` / `UNVERIFIABLE`)**: Uno o ambos objetos no residen en el catálogo canónico ni en la IR. Se emite un aviso de falta de contrato sin asumir éxito a ciegas.
- **Consecuencias**:
  - Positivas: Erradicación del cableado empírico o a ciegas; garantía formal de que ningún `.maxpat` emitido por Harmos contenga cables ilegales entre señales y mensajes.
  - Negativas: Requiere mantener contratos actualizados y exhaustivos para los objetos que interactúen en el patcher.
