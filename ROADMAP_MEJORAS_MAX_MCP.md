# Roadmap de Mejoras y Contribuciones Open Source: Max/MSP MCP Server

> **Documento Estratégico de Evolución de Herramientas Agénticas para Max/MSP**  
> *Objetivo:* Plan de auditoría técnica, mejoras funcionales y diseño de Pull Requests quirúrgicos para el ecosistema open source de servidores MCP en Max/MSP (`ersatzben/maxmsp-mcp` y `tiianhk/MaxMSP-MCP-Server`).

---

## 1. Contexto y Repositorios Objetivo

* **Repositorio Primario (Fork Activo & Extendido):** [https://github.com/ersatzben/maxmsp-mcp](https://github.com/ersatzben/maxmsp-mcp) (Ben Armstrong / BenCello). Licencia MIT.
* **Repositorio Upstream (Académico / ISMIR 2025):** [https://github.com/tiianhk/MaxMSP-MCP-Server](https://github.com/tiianhk/MaxMSP-MCP-Server) (Haokun Tian / Shuoyang Zheng). Licencia MIT.
* **Referencia Alternativa C++:** [https://github.com/signalcompose/MaxMCP](https://github.com/signalcompose/MaxMCP) (Signal Compose).

---

## 2. Diagnóstico de la Arquitectura Actual

El puente actual opera mediante una cadena de cuatro componentes:
```text
Cliente LLM (Claude Code / OpenCode / Cursor)
       ↕ stdio / SSE (JSON-RPC)
server.py (FastMCP en Python)
       ↕ Socket.IO (TCP localhost:5002)
max_mcp_node.js (Node for Max dentro del parche)
       ↕ Scripting Messages internos de Max
max_mcp.js / max_mcp_v8_add_on.js (Motor JS / V8 de Max)
```

### Fortalezas Detectadas
1. Validación preventiva en Python contra truncado numérico en JSON (`["25."]`).
2. Confirmación obligatoria de dirección de disparo en objetos `trigger` (`trigger_rtl=True`).
3. Herramientas básicas de subpatcher (`create_subpatcher`, `enter_subpatcher`, `exit_subpatcher`).
4. Algoritmo de posicionamiento libre de colisiones (`get_avoid_rect_position`).

---

## 3. Oportunidades Críticas de Mejora (Propuestas de PR)

A continuación se detallan las 5 áreas de mejora técnica estructuradas como futuras unidades de trabajo (*work units*) para contribuciones quirúrgicas:

### PR 1: Soporte para `gen~` y Manipulación de `[codebox]` (Prioridad Alta)
* **Problema:** En el upstream ([Issue #5](https://github.com/tiianhk/MaxMSP-MCP-Server/issues/5)), los usuarios reportan la imposibilidad de que el agente navegue o programe algoritmos dentro de `[gen~]`. Actualmente las herramientas de subpatcher solo admiten objetos `p`. Además, los LLMs destacan escribiendo código textual (GenExpr) antes que posicionando cajas visuales.
* **Propuesta:**
  1. Extender `enter_subpatcher` para reconocer objetos de clase `gen~` y acceder a su patcher interno.
  2. Implementar herramientas específicas:
     * `get_codebox_text(varname)`: Lee el código GenExpr actual dentro de una caja `[codebox]`.
     * `set_codebox_text(varname, genexpr_code)`: Inyecta y recompila código GenExpr en tiempo real.
* **Archivos a modificar:**
  * `server.py`: Definición de esquemas de herramientas y validación de sintaxis GenExpr básica.
  * `max_mcp.js` / `max_mcp_v8_add_on.js`: Lectura y escritura en la propiedad `boxtext` de objetos `codebox` mediante la API de Max Javascript.

---

### PR 2: Introspección de Buffers y Diccionarios (`buffer~`, `dict`, `coll`) (Prioridad Alta)
* **Problema:** El servidor actual es ciego al estado de los datos en tiempo de ejecución. El agente no puede verificar si un `buffer~` contiene audio cargado, cuál es su frecuencia de muestreo o su longitud en milisegundos, ni puede consultar estructuras complejas en objetos `dict`.
* **Propuesta:**
  1. `get_buffer_info(buffer_name)`:
     * Retorna: `{ exists: bool, duration_ms: float, sample_rate: int, channels: int, total_frames: int }`.
  2. `get_dict_content(dict_name)` / `set_dict_content(dict_name, json_data)`:
     * Permite sincronizar diccionarios de Max directamente con objetos JSON de Python/LLM.
* **Archivos a modificar:**
  * `server.py`: Nuevos endpoints FastMCP.
  * `max_mcp.js`: Uso de la clase nativa `Buffer` y `Dict` de Max JavaScript (`new Buffer(name)`, `new Dict(name)`).

---

### PR 3: Validación Semántica de Inlets/Outlets (Audio vs Control) (Prioridad Media)
* **Problema:** `connect_max_objects` intenta conectar puertos sin validar la compatibilidad de señal. Conectar una salida de audio (`~`) a una entrada que solo admite mensajes enteros produce un error silencioso en la consola de Max, pero el MCP reporta éxito.
* **Propuesta:**
  * Mantener una tabla de introspección de objetos canónicos de Max/MSP indicando qué inlets y outlets son de tipo señal (`signal`) y cuáles de tipo mensaje (`control`).
  * Lanzar una advertencia clara o rechazo temprano si se intenta conectar un outlet de señal a un inlet de control sin un objeto de conversión previo (como `snapshot~` o `peakamp~`).

---

### PR 4: Compatibilidad con Max for Live (M4L) y Objetos `live.*` (Prioridad Media)
* **Problema:** La suite actual rechaza activamente `live.dial` e ignora el ecosistema de Ableton Live.
* **Propuesta:**
  * Añadir un modo configurable `@env live` para permitir el uso seguro de `live.dial`, `live.slider`, `live.tab`, `live.numbox`, respetando sus rangos normalizados y unidades dBFS.
  * Añadir herramientas de navegación LOM de solo lectura (`get_live_track_info`, `get_live_device_parameters`).

---

### PR 5: Resiliencia de Transporte y Targeting Multi-Parche (Prioridad Baja/Estabilidad)
* **Problema:** Socket.IO corre en un puerto fijo (`5002`) sin manejo robusto de desconexiones si Max se cierra o se reinicia. Además, si hay dos parches abiertos con `node.script`, colisionan.
* **Propuesta:**
  * Protocolo de *heartbeat* (ping-pong) para reportar desconexión limpia en el cliente MCP.
  * Identificador único de sesión por parche (`patcher_id`) para asegurar que los comandos se apliquen a la ventana correcta.

---

## 4. Protocolo de Ejecución para las Contribuciones

Para mantener la máxima calidad e integridad (*surgical PR protocol*):

1. **Aislamiento de Entorno:**
   * Clonar `ersatzben/maxmsp-mcp` en una carpeta de desarrollo aislada o submódulo.
   * Probar cambios contra una instalación de Max 9 en Windows / macOS.
2. **Issue-First:**
   * Abrir un issue formal en GitHub antes de enviar código, explicando el caso de uso, la motivación arquitectónica y la retrocompatibilidad.
3. **Validación con Parches de Prueba:**
   * Cada PR debe acompañarse de un parche de prueba `.maxpat` reproducible donde se demuestre la funcionalidad antes y después del cambio.
4. **Higiene de Commits:**
   * Commits atómicos, limpios y descriptivos siguiendo la convención estándar (sin atribuciones automáticas).

---
*Roadmap establecido como guía de trabajo para potenciar las herramientas de conexión entre LLMs y Max/MSP.*
