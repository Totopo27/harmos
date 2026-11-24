# ADR 0012: Síntesis Dinámica de Aridad en el Motor de Contratos

- **Estado**: Aceptado
- **Fecha**: 2026-11-24
- **Contexto**: Primitivas de Max MSP como `unpack`, `pack`, `trigger`/`t`, `route` y `poly~` cambian la cantidad o el tipo de sus inlets y outlets en función de sus argumentos de instanciación o del subpatcher hospedado. Declaraciones estáticas fijas en `core/schema/max_contracts.json` provocan rechazos espurios o validaciones ciegas fuera de rango.
- **Decisión**: `ContractEngine` (`core/compiler/contract_engine.py`) implementa `_synthesize_dynamic_contract()` dentro de `get_object_contract()`:
  1. Para `unpack`, `pack`, `trigger`/`t` y `route`, sintetiza los puertos posicionales y sus tipos (`int`, `float`, `symbol`, `bang`, `list`, `anything`) a partir de los argumentos de la caja.
  2. Para `poly~`, resuelve el contrato superpuesto del subpatcher cuando su nombre figura en `_overlay_names`, o sintetiza puertos `@inlets N` / `@outlets M` dinámicamente preservando `poly~` estático como respaldo cuando no existen flags ni overlay.
- **Consecuencias**:
  - Positivas: Cobertura exacta de cajas polimórficas sin hardcodear excepciones por parche.
  - Negativas: Exige que todo subpatcher de voz que exceda la firma base declare sus puertos vía overlay IR o flags `@inlets`/`@outlets`.
