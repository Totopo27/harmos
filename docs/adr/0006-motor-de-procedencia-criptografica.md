# ADR 0006: Motor de Procedencia Criptográfica (emitted-from.json)

- **Estado**: Aceptado
- **Fecha**: 2026-11-23
- **Contexto**: Al sintetizar paquetes y patchers de Max MSP a partir de Representaciones Intermedias (IR) y código fuente externo, surge el riesgo de deriva inadvertida: modificaciones manuales en los archivos emitidos, alteraciones en las especificaciones IR o cambios en el catálogo canónico de contratos (`core/schema/max_contracts.json`) que invaliden las garantías de tipado.
- **Decisión**: Se implementa un motor de procedencia criptográfica en `core/compiler/provenance.py` que:
  1. Computa y estampa hashes SHA-256 normalizados (determinismo multiplataforma CRLF/LF) para contratos, IR, código fuente y artefactos emitidos en un archivo inmutable `emitted-from.json`.
  2. Proporciona una compuerta de verificación fail-closed (`harmos verify-provenance <path>`) con estados binarios inequívocos: `VALID`, `STALE_CONTRACTS`, `STALE_IR`, `STALE_SOURCE`, `STALE_ARTIFACTS`, `UNVERIFIABLE` e `INVALID`.
  3. Establece la regla de honestidad epistémica: ante evidencia ausente o contratos inaccesibles, el veredicto es categóricamente `UNVERIFIABLE`, nunca `VALID`.
- **Consecuencias**:
  - Positivas: Trazabilidad total de cada artefacto generado; detección inmediata de desincronización o manipulación manual.
  - Negativas: Se requiere mantener actualizado el archivo `emitted-from.json` si se regeneran deliberadamente los artefactos.
