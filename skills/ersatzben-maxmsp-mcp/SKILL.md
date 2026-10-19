---
name: ersatzben-maxmsp-mcp
description: "Trigger: ersatzben-maxmsp-mcp, maxmcp, parchear via mcp, modificar patch max en vivo. Reglas críticas y prevención de colisiones para parcheo Max/MSP vía MCP."
license: Apache-2.0
metadata:
  author: "OptimizandoParaMaxSDK"
  version: "1.1"
---

# Ersatzben MaxMSP MCP

## Activation Contract

Cargar al interactuar con parches de Max MSP a través de servidores MCP (`MaxMCP` o `ersatzben-maxmsp-mcp`) para crear objetos, conectar patchcords, manipular canvas en vivo o auditar grafos de señales.

## Hard Rules

- **Protocolo de Posicionamiento Mandatorio**: Consultar `get_avoid_rect_position()` antes de invocar `add_max_object`. Posicionar en `y = bottom + 50`; en la misma fila usar `x += ancho_previo + 25`. Prohibido solapar coordenadas.
- **Preservación Decimal en JSON**: Pasar argumentos float como strings con punto decimal (ej. `["0", "127", "0", "25."]`) o flags de tipo en `unpack` (`["f", "f", "f"]`) para impedir truncamiento a enteros.
- **Orden de Disparo Right-to-Left**: Respetar el flujo de ejecución temporal de derecha a izquierda en outlets de objetos `trigger` (`[t]`).
- **Auto-Summing de Entradas MSP**: Las entradas con tilde (`~`) suman automáticamente; prohibido intercalar `+~` únicamente para unir cables de audio.
- **Prohibición Absoluta de Conexiones a `comment`**: Las cajas `comment` carecen de inlets funcionales; validar que el destino nunca sea una caja `comment`.
- **Persistencia en `coll`**: Inicializar colecciones con el argumento `@embed 1` para no perder datos al cerrar el patcher.
- **Cero Errores en Log de Max**: Todo parche debe verificarse contra `Max.log` en `%APPDATA%\Cycling '74\Max X\Logs` certificando cero advertencias o errores.

## Decision Gates

| Situación de Parcheo | Condición Detectada | Acción Requerida |
| :--- | :--- | :--- |
| Nueva posición de objeto | Bounding box obtenido | Asignar `y = bottom + 50` o `x = prev_right + 25` |
| Argumentos con coma flotante | Serialización JSON estándar | Enviar literales string con punto decimal (`"25."`) |
| Mezcla de señales de audio | Múltiples fuentes MSP | Conectar directo al mismo inlet del receptor |
| Enrutamiento de patchcord | Destino tipo `comment` | Bloquear conexión; `comment` no tiene inlets |
| Almacenamiento con `coll` | Parche serializable | Agregar argumento explícito `@embed 1` |

## Execution Steps

1. Consultar rectángulos ocupados llamando a `get_avoid_rect_position()`.
2. Calcular coordenadas del nuevo objeto respetando márgenes mínimos de 50px verticales o 25px horizontales.
3. Formatear números en coma flotante como cadenas con punto decimal para preservar tipo `float` en Max.
4. Crear objetos verificando que ningún cable tenga como destino una caja `comment`.
5. Enlazar patchcords respetando el orden secuencial Right-to-Left de `trigger`.
6. Auditar `Max.log` buscando cadenas de error y confirmar estado limpio.

## Output Contract

- Comandos MCP ejecutados sin colisiones visuales ni superposiciones de cajas.
- Patcher libre de errores de conexión con validación limpia en `Max.log`.

## References

- `references/mcp-patching-mechanics.md` — Protocolo detallado de espaciado, tipado JSON, reglas de `dial` y depuración forense.
