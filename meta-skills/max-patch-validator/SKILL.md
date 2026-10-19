---
name: max-patch-validator
description: "Trigger: max-patch-validator, auditar patch max, verificar consola max. Audita consola de Max y valida tipado estricto de inlets y outlets en patchers."
license: Apache-2.0
metadata:
  author: "OptimizandoParaMaxSDK"
  version: "1.1"
---

# Max Patch Validator

## Activation Contract

Cargar al generar, ensamblar o modificar parches de Max MSP (`.maxpat`) o al probar externals compilados, para auditar la consola de Max y validar el tipado estricto de inlets y outlets.

## Hard Rules

- **Cero Hardcoding de Índices**: Prohibido cablear inlets o outlets por aproximación; gobernar toda conexión por los contratos de `core/schema/max_contracts.json`.
- **Inspección de Max Console Obligatoria**: Verificar activamente el log o captura de la Max Console antes de declarar un parche libre de errores.
- **Tipado Estricto de Cables**:
  - Validar índices especializados (ej. `midiformat`: inlet 0 nota, inlet 1 vel, inlet 5 pitch bend, inlet 6 canal).
  - Prohibido conectar listas compuestas directamente a inlets que esperan un único entero; insertar adaptadores idiomáticos (`unpack`).
- **Cero Tolerancia a Notificaciones Rojas**: Cualquier mensaje rojo (`can't connect`, `doesn't match type`, `no such object`) marca la compuerta como RECHAZADA.

## Decision Gates

| Síntoma de Error en Consola | Causa de Tipado | Acción Correctiva |
| :--- | :--- | :--- |
| `doesn't match type` | Lista hacia inlet escalar (`int` o `float`) | Intercalar `unpack` o `route` |
| `can't connect` | Conexión hacia objeto `comment` o inlet fuera de rango | Validar tipo de caja y corregir índice de inlet |
| Número truncado a entero | Objeto de control aritmético sin decimal | Añadir punto decimal en argumento (`+ 0.`) |
| `no such object` | External o abstracción no indexada | Reubicar archivo en la carpeta de búsqueda de Max |

## Execution Steps

1. Leer advertencias y errores de la Max Console o del archivo de log.
2. Identificar el objeto emisor, el objeto receptor y el índice del inlet/outlet en conflicto.
3. Consultar la especificación en `core/schema/max_contracts.json`.
4. Insertar los adaptadores de tipos de Max necesarios (`unpack`, `flonum`, `route`).
5. Recargar el patcher y capturar la consola para verificar cero notificaciones rojas.

## Output Contract

- Patcher corregido con ruteo de tipos conforme a contratos.
- Reporte de validación confirmando cero errores en la Max Console.

## References

- `references/patch-contracts.md` — Especificación de contratos de inlets/outlets y diagnóstico de la consola de Max.
