---
name: max-live-verifier
description: "Trigger: max-live-verifier, probar max en vivo, feedback visual consola. Ejecuta Max en vivo, audita consola y captura ventanas hasta lograr cero errores."
license: Apache-2.0
metadata:
  author: "OptimizandoParaMaxSDK"
  version: "1.1"
---

# Max Live Verifier

## Activation Contract

Cargar de forma obligatoria tras compilar externals (`.mxe64`), generar scripts o crear patchers (`.maxpat`) para ejecutar el bucle cerrado de verificación en vivo contra `Max.exe`.

## Hard Rules

- **Prohibido Finalizar sin Prueba en Vivo**: Ningún external o patch se considera finalizado sin levantarse y probarse en una instancia real de `Max.exe`.
- **Inspección Mandatoria de Consola**: Cualquier línea roja (error de sintaxis, símbolo no resuelto, tipos incompatibles o puerto roto) rechaza automáticamente la compuerta.
- **Inspección Visual de Objetos**: Verificar que los objetos visuales (JGraphics, `jsui` o interfaces generadas) se dibujen sin artefactos gráficos ni bordes rojos de error.
- **Bucle de Auto-Corrección Autónomo**: Ante fallos en la consola, extraer el error, alimentar la corrección al generador correspondiente y reintentar la prueba.

## Decision Gates

| Síntoma en Consola / UI | Causa Raíz Probable | Acción Correctiva Inmediata |
| :--- | :--- | :--- |
| `doesn't match "float"` | Incompatibilidad de cableado | Derivar a `max-patch-validator` para corregir adaptadores |
| `no such object` | Binario `.mxe64` no indexado | Copiar binario a `Packages/<suite>/externals/` |
| Excepción de memoria / crash | Fuga o acceso ilegal en C++ | Auditar punteros e hilos DSP/scheduler en Min-Devkit |
| Consola limpia y UI sin artefactos | Render y ejecución nominal | Declarar compuerta APROBADA (PASS) |

## Execution Steps

1. Desplegar el binario o patcher en la carpeta de Packages activa de Max en Windows.
2. Lanzar `Max.exe` con el archivo de prueba mediante comando o script de PowerShell.
3. Activar el foco de ventana y ejecutar script de captura visual (`capturar.ps1`).
4. Analizar la imagen capturada e inspeccionar el log de la Max Console.
5. Determinar veredicto (PASS / FAIL).
6. Si falla, derivar el error técnico exacto al generador para corrección y re-evaluación.

## Output Contract

- Reporte de verificación en vivo con estado de ejecución de `Max.exe`.
- Captura visual de evidencia de la interfaz del patcher.
- Veredicto binario (PASS/FAIL) certificando cero errores en la Max Console.

## References

- `references/live-verification-loop.md` — Arquitectura del bucle de verificación, captura de pantallas y diagnóstico de fallos.
