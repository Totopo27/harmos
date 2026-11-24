# ADR 0015: Guardrail Pre-Commit Fail-Closed (scripts/check.py)

- **Estado**: Aceptado
- **Fecha**: 2026-11-24
- **Contexto**: Escaneos de seguridad limitados a archivos ya agregados al índice Git dejan escapar fugas en archivos nuevos no trackeados, y fallos parciales de subprocesos o errores silenciosos de formato en `core/schema/` pueden pasar desapercibidos hasta después de subir cambios al repositorio remoto.
- **Decisión**: `scripts/check.py` implementa una puerta pre-commit fail-closed en tres pasos secuenciales:
  1. Ejecuta la suite completa (`python -m unittest discover tests`) anclada a `_REPO_ROOT`.
  2. Valida la sintaxis JSON de `core/schema/*.json` y la estructura integral de `max_contracts.json` vía `validate_contracts()`.
  3. Invoca `git ls-files --cached --others --exclude-standard` fallando en cerrado si Git retorna error, rechaza scripts locales prohibidos (`*.ps1`, `*.bat`, `*.cmd`) y escanea archivos trackeados y no trackeados contra rutas absolutas de host (Windows, Linux, macOS) y tokens/claves privadas (`ghp_`, `gho_`, `github_pat_`, `AKIA`, claves PEM).
- **Consecuencias**:
  - Positivas: Detección temprana de regresiones, contratos corruptos y fugas de privacidad antes de cualquier commit.
  - Negativas: Documentación y plantillas deben usar marcadores simbólicos en lugar de rutas absolutas de ejemplo.
