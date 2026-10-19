---
name: max-runtime-gatekeeper
description: "Trigger: max-runtime-gatekeeper, auditar consola max, gatekeeper runtime max, feedback loop max. Compila, ejecuta Max en vivo, audita consola y valida patchers a cero errores."
license: Apache-2.0
metadata:
  author: "Harmos Core Team"
  version: "1.0.0"
---

# Max Runtime Gatekeeper

## Activation Contract

Cargar de forma obligatoria tras generar cualquier external compilado (`.mxe64`), script o patcher (`.maxpat`) mediante Harmos, para ejecutar el bucle de validación en vivo y linteo estricto de conexiones.

## Hard Rules

- **Cero Tolerancia a Líneas Rojas**: Cualquier advertencia o error en `Max.log` (`doesn't match type`, `no such object`, `can't connect`, crasheo de proceso) marca la compuerta como **RECHAZADA (FAIL)**.
- **Validación Estricta de Tipos de Cables**:
  - Toda conexión debe coincidir con `core/schema/max_contracts.json`.
  - Prohibido conectar cables a cajas `comment` (carecen de inlets funcionales).
  - Validar índices de `midiformat`: 0=Pitch, 1=Velocity, 5=Pitch Bend, 6=Channel.
- **Verificación en Instancia Real**: Ningún paquete se certifica sin levantar la prueba en `Max.exe` y verificar la ausencia de fallos en el log del sistema.
- **Bucle de Auto-Corrección Autónomo**: Ante fallo de consola, extraer el desajuste exacto, corregir la llamada en el generador de parches o código C++ y reintentar.

## Decision Gates

| Error Detectado en Consola | Causa Raíz | Acción Correctiva de la Compuerta |
| :--- | :--- | :--- |
| `doesn't match type` | Tipado incorrecto en patchcord | Insertar adaptador idiomático (`unpack`, `flonum`) |
| `no such object` | Binario o package no indexado | Verificar copiado de `.mxe64` en carpeta de Packages |
| `connecting to comment` | Cable conectado a etiqueta | Eliminar cable hacia caja `comment` |
| Crasheo / Access Violation | Bloqueo en hilo de audio DSP | Auditar punteros nulos o `malloc` en `perform64` |

## Execution Steps

1. Compilar los externals de C++ mediante CMake y desplegar binarios en la suite de Packages.
2. Lintear el patcher de prueba con `TypedPatch` verificando que no existan desajustes de contratos.
3. Iniciar `Max.exe` con el archivo `.maxpat` de prueba.
4. Auditar el log interno de Max (`Max.log`) buscando cadenas de advertencia o fallo.
5. Si el log tiene 0 errores, emitir veredicto **PASS**. Si reporta errores, aplicar la acción de la compuerta y reintentar.

## Output Contract

- Veredicto binario de aprobación (PASS / FAIL).
- Certificación de cero errores en la consola de Max y patcher funcional verificado.

## References

- `core/schema/max_contracts.json` — Contratos de tipos de entradas y salidas.
- `docs/PROTOCOLO_SEGURIDAD_Y_PUBLICACION_GIT.md` — Estándar de higiene y pre-commit.
