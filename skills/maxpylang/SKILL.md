---
name: maxpylang
description: "Trigger: maxpylang, crear parche maxpat, amxd max for live python. Genera parches .maxpat y dispositivos .amxd usando MaxPyLang en Python."
license: Apache-2.0
metadata:
  author: "Barnard-PL-Labs / adaptado para ecosistema Max AI"
  version: "1.0.0"
---

# MaxPyLang

## Activation Contract

Cargar al generar programáticamente parches de Max MSP (`.maxpat`) o dispositivos Max for Live (`.amxd`), sintetizadores con múltiples osciladores, bancos de filtros o conexiones masivas sin colisiones visuales.

## Hard Rules

- **Desempaquetar Retorno de `place()`**: `patch.place()` SIEMPRE retorna una lista; indexar con `[0]` al asignar variables individuales (ej. `osc = patch.place("cycle~ 440")[0]`).
- **Nombres Case-Sensitive de Max**: Usar nombres exactos de la nomenclatura de Max (`cycle~`, `lores~`, `live.dial`).
- **Control de Posición Previo**: Invocar `patch.set_position(x, y)` antes de cada llamada a `place()` para prevenir superposición de cajas.
- **Indexación Cero de Conexiones**: Inlets y outlets se indexan en base 0 (`obj.ins[0]`, `obj.outs[0]`).
- **Limitador de Seguridad en M4L**: Insertar obligatoriamente `clip~ -1. 1.` antes de alimentar `plugout~`.
- **Salida Estéreo Completa**: Conectar siempre ambos canales de audio a `plugout~` (`ins[0]` e `ins[1]`).

## Decision Gates

| Requerimiento de Proyecto | Herramienta | Método de Guardado |
| :--- | :--- | :--- |
| Parche `.maxpat` desde cero o masivo | MaxPyLang (Python) | `patch.save("synth.maxpat")` |
| Dispositivo Instrumento M4L | MaxPyLang (Python) | `patch.save("synth.amxd", device_type="instrument")` |
| Dispositivo Efecto Audio M4L | MaxPyLang (Python) | `patch.save("fx.amxd", device_type="audio_effect")` |
| Dispositivo Efecto MIDI M4L | MaxPyLang (Python) | `patch.save("arp.amxd", device_type="midi_effect")` |
| Edición interactiva en caliente (Max abierto) | Servidor MCP (MaxMCP) | Herramientas MCP en tiempo real |

## Execution Steps

1. Instanciar `patch = mp.MaxPatch()`.
2. Establecer constantes de layout (`Y_STEP = 40`, `COL_WIDTH = 160`, `SECTION_GAP = 80`).
3. Posicionar el cursor con `patch.set_position(x, y)` y crear cada objeto desempaquetando `[0]`.
4. Conectar pares `[emisor.outs[n], receptor.ins[m]]` agrupados por bloques funcionales con `patch.connect()`.
5. Si el destino es `.amxd`, intercalar `clip~ -1. 1.` y mapear controles a objetos `live.*`.
6. Compilar y guardar mediante `patch.save(filename, device_type=...)`.

## Output Contract

- Script de Python generador ejecutable y reproducible.
- Archivo `.maxpat` o `.amxd` generado libre de colisiones visuales.

## References

- `assets/canonical-patterns.py` — Patrones de código para audio Max, instrumento M4L y síntesis aditiva iterativa.
- `references/m4l-dsl-guide.md` — Especificación de tipos de dispositivos M4L, reglas de layout y salvaguardas.
