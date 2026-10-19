# Catálogo de Herramientas, MCPs y Skills para Max/MSP & Max SDK
> **Ecosistema Especializado para Max/MSP, Max for Live (M4L), Max SDK (C/C++), Audio DSP & Automatización Agéntica con IA**  
> *Compilación de servidores MCP, skills de LLM, herramientas nativas, bibliotecas C/C++, motores de inferencia neuronal y puentes de desarrollo con IA.*

---

## Índice
1. [Visión y Separación Arquitectónica](#1-visión-y-separación-arquitectónica)
2. [Servidores MCP para Max/MSP & Ableton Live](#2-servidores-mcp-para-maxmsp--ableton-live)
   - 2.1. [MaxMCP (Signal Compose) — Servidor Nativo C++](#21-maxmcp-signal-compose--servidor-nativo-c)
   - 2.2. [MaxMSP MCP Server (ersatzben / dropcontrol) — Puente WebSocket / Node](#22-maxmsp-mcp-server-ersatzben--dropcontrol--puente-websocket--node)
   - 2.3. [MaxMSP-MCP Server (tiianhk - ISMIR 2025) — Programación Agéntica](#23-maxmsp-mcp-server-tiianhk---ismir-2025--programación-agéntica)
   - 2.4. [bach-mcp (agustinissidoro) — Composición Algorítmica & Notación](#24-bach-mcp-agustinissidoro--composición-algorítmica--notación)
   - 2.5. [Producer Pal (adamjmurray) — Servidor MCP en Max for Live](#25-producer-pal-adamjmurray--servidor-mcp-en-max-for-live)
   - 2.6. [Loophole (OthmanAdi) — Puente MCP para Ableton Live 12](#26-loophole-othmanadi--puente-mcp-para-ableton-live-12)
3. [DSLs Simbólicos y Generación Programática de Parches](#3-dsls-simbólicos-y-generación-programática-de-parches)
   - 3.1. [El Problema de la Serialización JSON Cruda en LLMs](#31-el-problema-de-la-serialización-json-cruda-en-llms)
   - 3.2. [py2max & MaxPy — Compiladores de Python a .maxpat](#32-py2max--maxpy--compiladores-de-python-a-maxpat)
   - 3.3. [py-js — Python 3 Embebido Nativo en Max](#33-py-js--python-3-embebido-nativo-en-max)
4. [Inferencia Neuronal & Deep Learning DSP en Tiempo Real (C++ / SDK)](#4-inferencia-neuronal--deep-learning-dsp-en-tiempo-real-c--sdk)
   - 4.1. [nn~ & LibTorch (IRCAM) — Modelos Generativos y RAVE](#41-nn--libtorch-ircam--modelos-generativos-y-rave)
   - 4.2. [Repositorios RAVE en Hugging Face](#42-repositorios-rave-en-hugging-face)
   - 4.3. [RTNeural & RTNeural_Plugin (Sam Pluta / Jatin Chowdhury)](#43-rtneural--rtneural_plugin-sam-pluta--jatin-chowdhury)
   - 4.4. [Neural Amp Modeler (NAM) & neural_tilde — Modelado Analógico](#44-neural-amp-modeler-nam--neural_tilde--modelado-analógico)
   - 4.5. [Neutone SDK (Qosmo) — Empaquetado Universal de Modelos IA](#45-neutone-sdk-qosmo--empaquetado-universal-de-modelos-ia)
   - 4.6. [FluCoMa & Data Knot / SP-Tools — Machine Listening & Corpus](#46-flucoma--data-knot--sp-tools--machine-listening--corpus)
5. [Skills y Guías Agénticas Especializadas para Max/MSP](#5-skills-y-guías-agénticas-especializadas-para-maxmsp)
   - 5.1. [Skill: `ersatzben-maxmsp-mcp-maxmsp` (Reglas Críticas de Parcheo)](#51-skill-ersatzben-maxmsp-mcp-maxmsp-reglas-críticas-de-parcheo)
   - 5.2. [Skill: `patch-guidelines` & `organize-patch`](#52-skill-patch-guidelines--organize-patch)
   - 5.3. [Skill: `max-techniques` (Patrones Avanzados de Max)](#53-skill-max-techniques-patrones-avanzados-de-max)
   - 5.4. [Skill: `m4l-techniques` (Live Object Model & Ableton)](#54-skill-m4l-techniques-live-object-model--ableton)
   - 5.5. [Skill: `genexpr-dsp` (Optimización y Sintaxis de gen~)](#55-skill-genexpr-dsp-optimización-y-sintaxis-de-gen)
   - 5.6. [Skill: `py2max-generator` (Generación Limpia con DSL)](#56-skill-py2max-generator-generación-limpia-con-dsl)
   - 5.7. [Skill: `max-sdk-neural-audio` (C++ DSP & Concurrencia Lock-Free)](#57-skill-max-sdk-neural-audio-c-dsp--concurrencia-lock-free)
6. [Arsenal Max SDK: Desarrollo C / Modern C++ (min-devkit)](#6-arsenal-max-sdk-desarrollo-c--modern-c-min-devkit)
   - 6.1. [Max SDK Oficial (Cycling '74)](#61-max-sdk-oficial-cycling-74)
   - 6.2. [min-devkit (C++17 Declarativo)](#62-min-devkit-c17-declarativo)
   - 6.3. [Librerías C++ Esenciales para Audio DSP & Rendimiento](#63-librerías-c-esenciales-para-audio-dsp--rendimiento)
7. [Nutrición Cruzada desde el Catálogo General](#7-nutrición-cruzada-desde-el-catálogo-general)
   - 7.1. [IPC Lock-Free & Concurrencia de Alto Rendimiento](#71-ipc-lock-free--concurrencia-de-alto-rendimiento)
   - 7.2. [Auditoría Estática y Fuzzing de Binarios C/C++](#72-auditoría-estática-y-fuzzing-de-binarios-cc)
   - 7.3. [Higiene de Commits Quirúrgicos (`work-unit-commits` & `surgical-pr`)](#73-higiene-de-commits-quirúrgicos-work-unit-commits--surgical-pr)
   - 7.4. [Generador de Arquitecturas y Flujos de Datos (`archify`)](#74-generador-de-arquitecturas-y-flujos-de-datos-archify)
8. [Estructura del Repositorio y Hoja de Ruta](#8-estructura-del-repositorio-y-hoja-de-ruta)

---

## 1. Visión y Separación Arquitectónica

Este catálogo vive de forma **independiente** en el ecosistema Harmos para mantener el foco en:
* **Programación de audio en tiempo real y DSP determinista**.
* **Extensiones nativas en C/C++ (externals para Max y Max for Live)**.
* **Control agéntico con LLMs (Claude, GPT, modelos locales) a través de MCP**.
* **Inferencia de modelos neuronales (LibTorch, RTNeural, ONNX) en el hilo de audio sin clicks ni bloqueos de memoria**.

Cubre la intersección entre **inteligencia artificial generativa, modelos de deep learning de audio y el entorno de ejecución gráfica y DSP de Cycling '74 Max & Ableton Live**.

---

## 2. Servidores MCP para Max/MSP & Ableton Live

Los servidores MCP (Model Context Protocol) permiten a un agente de IA interactuar de forma bidireccional con parches de Max y sesiones de Live.  
*(Para un análisis exhaustivo de debilidades, oportunidades de mejora y plan de Pull Requests para estos servidores, consultar el documento dedicado: [`ROADMAP_MEJORAS_MAX_MCP.md`](./ROADMAP_MEJORAS_MAX_MCP.md)).*

### 2.1. MaxMCP (Signal Compose) — Servidor Nativo C++
* **Repositorio Oficial:** [https://github.com/signalcompose/MaxMCP](https://github.com/signalcompose/MaxMCP)
* **Arquitectura:**
  ```text
  Claude Code / OpenCode (Cliente MCP)
         ↕ stdio (JSON-RPC)
  Node.js Bridge (websocket-mcp-bridge.js)
         ↕ WebSocket (puerto 7400)
  [maxmcp] External Nativo C++ (maxmcp.mxo / maxmcp.mxe64)
         ↕ Max API interna
  Parches de Max/MSP (.maxpat)
  ```
* **Características Clave:**
  * **Zero-config:** Se inserta el objeto `[maxmcp @mode agent @port 7400]` para el servidor global.
  * **30 herramientas MCP:** Inspección de parches, adición/eliminación de objetos, conexión de patchcords con verificación de puertos, cálculo de layout anti-colisión (`get_avoid_rect_position`), logs de consola y gestión de subpatchers.

---

### 2.2. MaxMSP MCP Server (ersatzben / dropcontrol) — Puente WebSocket / Node
* **Repositorios:** [https://github.com/ersatzben/maxmsp-mcp](https://github.com/ersatzben/maxmsp-mcp) / [dropcontrol/MaxMSP-MCP-Server-multipatch](https://github.com/dropcontrol/MaxMSP-MCP-Server-multipatch)
* **Enfoque:** Implementación en Node.js que conecta mediante WebSockets y mensajes de scripting con parches de Max. Ideal para prototipado rápido sin compilar binarios nativos C++.

---

### 2.3. MaxMSP-MCP Server (tiianhk - ISMIR 2025) — Programación Agéntica
* **Repositorio:** [https://github.com/tiianhk/MaxMSP-MCP-Server](https://github.com/tiianhk/MaxMSP-MCP-Server)
* **Referencia Científica:** ISMIR 2025 Late-Breaking Demo: *“Agentic Max/MSP Programming with LLMs and MCP”*.
* **Características:**
  * Diseñado específicamente para evaluar y resolver las limitaciones de los LLMs en lenguajes visuales de flujo de datos (*visual dataflow*).
  * Incluye herramientas de análisis semántico del parche para que el modelo razone sobre el flujo de señales (audio vs control) antes de realizar modificaciones.

---

### 2.4. bach-mcp (agustinissidoro) — Composición Algorítmica & Notación
* **Repositorio:** [https://github.com/agustinissidoro/bach-mcp](https://github.com/agustinissidoro/bach-mcp)
* **Propósito:** Puente MCP para la suite **bach** (*automated composer's helper*) en Max.
* **Herramientas:**
  * Control y consulta de `bach.roll` y `bach.score`.
  * Escritura algorítmica de partituras y rollos microtonales desde lenguaje natural.
  * Compatible con proveedores locales (llama.cpp / Ollama) y APIs en la nube.

---

### 2.5. Producer Pal (adamjmurray) — Servidor MCP en Max for Live
* **Repositorio & Web:** [https://github.com/adamjmurray/producer-pal](https://github.com/adamjmurray/producer-pal) | [producer-pal.org](https://producer-pal.org/)
* **Arquitectura:**
  * Empaquetado como un dispositivo nativo **Max for Live** (`Producer_Pal.amxd`).
  * Utiliza **Node for Max** internamente para levantar el servidor MCP.
* **Ventajas:**
  * No requiere scripts de control remoto de Python en carpetas de sistema de Ableton.
  * Acceso directo al **LOM (Live Object Model)**: control de clips, notas MIDI, parámetros de sintetizadores, transporte, escenas y pistas.

---

### 2.6. Loophole (OthmanAdi) — Puente MCP para Ableton Live 12
* **Repositorio:** [https://github.com/OthmanAdi/loophole](https://github.com/OthmanAdi/loophole)
* **Características:**
  * Opera sobre el Extension Host persistente de Live 12 con Node.js.
  * Diseñado con cola de escritura (`WriteQueue`) para evitar condiciones de carrera al modificar sets en vivo.
  * Incluye skill lista para instalar: `npx skills add OthmanAdi/loophole --skill ableton-live`.

---

## 3. DSLs Simbólicos y Generación Programática de Parches

### 3.1. El Problema de la Serialización JSON Cruda en LLMs
Un archivo `.maxpat` es un JSON gigante que define coordenadas en pantalla (`patching_rect: [x, y, w, h]`), identificadores únicos arbitrarios (`obj-12`, `box_1`) y un índice numérico estricto de entradas y salidas. 
Pedirle a un LLM que escriba directamente un `.maxpat` suele resultar en:
1. Conexiones invertidas entre inlets de control e inlets de audio (`~`).
2. Cajas sobrepuestas en las mismas coordenadas.
3. Desajustes en tipos numéricos (JSON borra el `.0` de los floats).

### 3.2. `MaxPyLang` & `py2max` — Compiladores de Python a .maxpat y .amxd
La solución más sólida identificada en la literatura (*Benchmarking LLM Code Generation for Audio Programming with Visual Dataflow Languages*, NIME / arXiv) es hacer que el LLM escriba un script en un DSL de alto nivel en Python que compila automáticamente a un `.maxpat` perfecto.

* **`Barnard-PL-Labs/MaxPyLang` (Evolución de MaxPy):** [https://github.com/Barnard-PL-Labs/MaxPyLang](https://github.com/Barnard-PL-Labs/MaxPyLang)
  * Publicado en PyPI (`pip install maxpylang`). Desarrollado por Barnard College / Columbia University.
  * Soporte nativo para generar **dispositivos Max for Live (`.amxd`)** mediante el flag `device_type="instrument" | "audio_effect" | "midi_effect"`.
  * Diseñado con soporte de primera clase para agentes de IA (`maxpylang setup-claude`), validación preventiva de inlets/outlets y stubs tipados para autocompletado en IDEs.
  * Ver el skill dedicado en el repositorio: [`skills/maxpylang/SKILL.md`](./skills/maxpylang/SKILL.md) y plantilla en [`templates/maxpylang_template.py`](./templates/maxpylang_template.py).

* **`shakfu/py2max`:** [https://github.com/shakfu/py2max](https://github.com/shakfu/py2max)
  * Generación declarativa de objetos, bpatchers, subpatchers y conexiones.
  * Cálculo automático de layout y posicionamiento vertical/horizontal sin colisiones.
  ```python
  from py2max import Patcher
  
  p = Patcher('synth.maxpat')
  osc = p.add_textbox('cycle~ 440')
  gain = p.add_textbox('gain~')
  dac = p.add_textbox('ezdac~')
  
  p.link(osc, gain)
  p.link(gain, dac)
  p.save()
  ```

### 3.3. `py-js` — Python 3 Embebido Nativo en Max
* **Repositorio:** [https://github.com/shakfu/py-js](https://github.com/shakfu/py-js)
* **Descripción:** External en C con bindings de Cython que incrusta un runtime de Python 3 completo dentro del proceso de Max. Permite ejecutar librerías como NumPy, SciPy o clientes de API de IA directamente desde un objeto `[py]` en el parche.

---

## 4. Inferencia Neuronal & Deep Learning DSP en Tiempo Real (C++ / SDK)

Esta categoría agrupa los motores de inferencia optimizados para ejecutar modelos de Deep Learning en el hilo de audio en tiempo real dentro de Max SDK.

### 4.1. `nn~` & LibTorch (IRCAM) — Modelos Generativos y RAVE
* **Repositorio:** [https://github.com/acids-ircam/nn_tilde](https://github.com/acids-ircam/nn_tilde)
* **Desarrollador:** Antoine Caillon / ACIDS IRCAM.
* **Arquitectura:**
  * External en C++ nativo para Max/MSP y Pure Data.
  * Enlace directo con **LibTorch** (runtime C++ de PyTorch).
  * Incluye versiones multicanal: `[mc.nn~]` y `[mcs.nn~]`.
  * Modo síncrono e hiper-optimizado (*Lazy Mode*) para ejecución sin cortes de audio.

### 4.2. Repositorios RAVE en Hugging Face
Los modelos entrenados con RAVE (*Realtime Audio Variational autoEncoder*) se exportan como archivos TorchScript (`.ts`) y se cargan directamente en `[nn~]`:
* **Intelligent Instruments Lab:** [https://huggingface.co/Intelligent-Instruments-Lab/rave-models](https://huggingface.co/Intelligent-Instruments-Lab/rave-models) (Modelos de percusión, cuerdas, voz y síntesis neuronal).
* **Tangible Music Lab:** [https://huggingface.co/Tangible-Music-Lab/RAVE_models](https://huggingface.co/Tangible-Music-Lab/RAVE_models) (Modelos de síntesis y timbre transfer en tiempo real).

### 4.3. RTNeural & `RTNeural_Plugin` (Sam Pluta / Jatin Chowdhury)
* **Repositorios:** [jatinchowdhury18/RTNeural](https://github.com/jatinchowdhury18/RTNeural) | [spluta/RTNeural_Plugin](https://github.com/spluta/RTNeural_Plugin)
* **Características:**
  * Motor de inferencia en C++ para redes neuronales tradicionales (Dense, GRU, LSTM, Conv1D) diseñado específicamente para **DSP de audio en tiempo real**.
  * **Garantía RT-Safe:** Cero llamadas a `malloc`/`free` durante el procesamiento; aceleración vectorial con AVX2/NEON.
  * Sam Pluta compiló los objetos `[rtneural]` y `[rtneural~]` para Max/MSP, permitiendo cargar pesos entrenados en Python (Keras/PyTorch) y ejecutarlos con latencia despreciable.

### 4.4. Neural Amp Modeler (NAM) & `neural_tilde` — Modelado Analógico
* **Repositorios:** [apresta/neural_tilde](https://github.com/apresta/neural_tilde) | [mikeoliphant/NeuralAudio](https://github.com/mikeoliphant/NeuralAudio)
* **Características:**
  * External C++ que ejecuta modelos de **Neural Amp Modeler (NAM)** dentro de Max/MSP y Max for Live.
  * Emulación de amplificadores a válvulas, distorsiones analógicas y saturación no lineal con calidad de estudio.
  * Miles de modelos `.nam` disponibles de forma gratuita en sitios como [Tone3000](https://tone-3000.com) y Hugging Face.

### 4.5. Neutone SDK (Qosmo) — Empaquetado Universal de Modelos IA
* **Repositorio:** [https://github.com/Neutone/neutone_sdk](https://github.com/Neutone/neutone_sdk)
* **Creador:** Nao Tokui / Qosmo.
* **Propósito:** SDK open source para empaquetar modelos de PyTorch en tiempo real para usarlos en producción musical. Compatible con Max mediante el plugin VST3 `vst~ [NeutoneFX]`.

### 4.6. FluCoMa & Data Knot / SP-Tools — Machine Listening & Corpus
* **Sitio Oficial:** [https://www.flucoma.org/](https://www.flucoma.org/)
* **Data Knot (SP-Tools):** [https://discourse.flucoma.org/t/data-knot...](https://discourse.flucoma.org/t/data-knot-previously-known-as-sp-tools-machine-learning-tools-for-low-latency-real-time-performance/1594)
* **Aporte:** Suite nativa para Max de machine learning no supervisado: análisis de descriptores tímbricos, segmentación de audio en tiempo real, reducción de dimensionalidad (PCA, UMAP) y regresión (MLPRegressor) para control gestual y síntesis por corpus.

---

## 5. Skills y Guías Agénticas Especializadas para Max/MSP

Estas habilidades enseñan al agente de IA las **reglas de diseño, restricciones de tiempo real y sintaxis crítica** antes de escribir código o generar parches.

---

### 5.1. Skill: `ersatzben-maxmsp-mcp-maxmsp` (Reglas Críticas de Parcheo)
* **Origen:** [LobeHub](https://lobehub.com/skills/ersatzben-maxmsp-mcp-maxmsp) | [GitHub](https://github.com/ersatzben/maxmsp-mcp)
* **Reglas de Oro:**
  1. **Evitar colisiones:** Consultar siempre `get_avoid_rect_position()`.
  2. **Truncado numérico en JSON:** Enviar floats matemáticos con punto (`"25."`) como strings para evitar que JSON pierda el `.0`.
  3. **Dirección en `trigger` (`t`):** Disparo estricto de **derecha a izquierda (Right-to-Left)**.
  4. **Sumador automático en MSP (`~`):** Las entradas de señal suman automáticamente; no insertar `+~` redundantes para mezclar cables.
  5. **Controles `dial`:** `@size 1` con `@floatoutput 1` para rangos normalizados 0.0 a 1.0.

---

### 5.2. Skill: `patch-guidelines` & `organize-patch`
* **Origen:** MaxMCP Plugin ([signalcompose/MaxMCP](https://github.com/signalcompose/MaxMCP))
* **Propósito:** Convenciones de nomenclatura para `varname`, espaciado estándar y pipeline de 8 fases para ordenar visualmente parches desordenados.

---

### 5.3. Skill: `max-techniques` (Patrones Avanzados de Max)
* **Patrones Cubiertos:**
  * **Arquitectura `poly~`:** Polifonía dinámica y muteo de voces inactivas (`mute 1 0`).
  * **Abstracciones `bpatcher`:** Módulos reusables con interfaz GUI personalizada.
  * **Persistencia con `pattr` & `pattrstorage`:** Gestión y morphing de presets.

---

### 5.4. Skill: `m4l-techniques` (Live Object Model & Ableton)
* **Propósito:** Creación de dispositivos Max for Live (M4L) para Ableton Live.
* **Conceptos:**
  * **LOM (Live Object Model):** Navegación `path` → `id` → `live.object` → `live.observer`.
  * **Aislamiento de Espacio de Nombres:** Diferencia entre `---` (prefijo local de Live) y `#0` (identificador clásico de Max).
  * **Mapeo de Controles:** `live.dial` con curvas de automatización dBFS nativas.

---

### 5.5. Skill: `genexpr-dsp` (Optimización y Sintaxis de gen~)
* **Propósito:** Instrucciones para que el LLM escriba código en el operador `[codebox]` de `gen~` / GenExpr.
* **Puntos Críticos:**
  * Procesamiento *sample-by-sample* sin latencia de bloque de audio.
  * Manejo correcto de operadores de retardo unitario: `history` y `delay`.
  * Prevención de ramas condicionales pesadas (`if/else` en DSP) usando funciones matemáticas continuas o ternarios optimizados.
  * Manejo de buffers compartidos (`data` y `buffer`) en GenExpr.

---

### 5.6. Skill: `py2max-generator` (Generación Limpia con DSL)
* **Propósito:** Instruir al LLM a no generar JSON crudo directamente, sino emitir scripts concisos en Python usando `py2max`.
* **Beneficio:** 100% de parches válidos sin cables rotos ni cajas superpuestas.

---

### 5.7. Skill: `max-sdk-neural-audio` (C++ DSP & Concurrencia Lock-Free)
* **Propósito:** Reglas de desarrollo seguro en C++ con Max SDK / min-devkit al integrar modelos de IA:
  * **Nunca asignar memoria dinámica** (`malloc`, `new`, `std::vector::push_back`) dentro del método `perform` (Audio Thread).
  * **Uso de Colas SPSC Lock-Free:** Comunicación entre el hilo de cálculo o inferencia (Background Thread) y el hilo de audio mediante ringbuffers como `readerwriterqueue`.
  * **Manejo de Instrucciones SIMD:** Compilación con soporte AVX2 / NEON para acelerar capas densas o convolucionales.

---

## 6. Arsenal Max SDK: Desarrollo C / Modern C++ (min-devkit)

### 6.1. Max SDK Oficial (Cycling '74)
* **Repositorio:** [Cycling74/max-sdk](https://github.com/Cycling74/max-sdk) (v8.2.0 o superior).
* **Uso:** API clásica en C puro (`max-sdk-base`). Esencial para externals legacy o bindings directos con librerías nativas en C.

### 6.2. `min-devkit` (Modern C++ para Max)
* **Repositorio:** [Cycling74/min-devkit](https://github.com/Cycling74/min-devkit)
* **Ventajas:**
  * Sintaxis declarativa C++17 (`min::inlet<>`, `min::outlet<>`, `min::attribute<>`).
  * Generación automática de UI y documentación de ayuda (`.maxhelp`).
  * Primitivas seguras para concurrencia de audio (`min::fifo`).

### 6.3. Librerías C++ Esenciales para Audio DSP & Rendimiento
1. **nlohmann/json:** Serialización ultrarrápida de diccionarios y estructuras de datos en C++.
2. **libwebsockets / civetweb:** Creación de endpoints WebSocket internos para conectar Max con interfaces web o LLMs locales.
3. **KissFFT / PocketFFT / Intel IPP:** Procesamiento espectral y FFT de baja latencia dentro del hilo de audio.
4. **MoodyCamel ConcurrentQueue (`readerwriterqueue`):** Ringbuffer de productor único / consumidor único (SPSC) **lock-free** y libre de asignación de memoria, ideal para transferir datos de inferencia entre hilos sin causar cortes de audio (*clicks*).

---

## 7. Nutrición Cruzada de Metodologías de Ingeniería

Técnicas de ingeniería que potencian el desarrollo en Max SDK:

### 7.1. IPC Lock-Free & Concurrencia de Alto Rendimiento
* **Aplicación:** Técnicas de comunicación entre procesos (IPC por memoria compartida o sockets/named pipes) para transferir audio multicanal o tensores de pesos entre Max/MSP y programas externos (Python, PyTorch, Rust) con latencia cercana a cero.

### 7.2. Auditoría Estática y Fuzzing de Binarios C/C++
* **Aplicación:**
  * Análisis estático de código C++ para detectar *memory leaks* o punteros nulos antes de cargar el `.mxe64` en Max (un fallo de segmentación en un external crashea todo Max.exe).
  * Uso de sanitizers (AddressSanitizer / UndefinedBehaviorSanitizer) al compilar con MSVC en Visual Studio 2022.

### 7.3. Higiene de Commits Quirúrgicos (`work-unit-commits` & `surgical-pr`)
* **Aplicación:** Al trabajar en paquetes de Max que combinan código fuente C++, CMake, parches `.maxpat` y archivos JSON, cada cambio debe aislarse en unidades de trabajo atómicas para evitar mezclar cambios binarios con lógica de DSP.

### 7.4. Generador de Arquitecturas y Flujos de Datos (`archify`)
* **Aplicación:** Generación de diagramas de flujo de señales de audio, ruteo de matrices y diagramas de estados (state machines) para documentar patchers complejos y arquitecturas DSP.

---

## 8. Estructura del Repositorio y Hoja de Ruta

Estructura de trabajo en Harmos:

```text
harmos/
├── GUIA_MAX_SDK_PASO_A_PASO.md       <-- Guía maestra de compilación C/C++, DSP y Visual Studio
├── HERRAMIENTAS_Y_SKILLS_MAX.md     <-- Este catálogo maestro de herramientas, MCPs, IA y DSP
├── ROADMAP_MEJORAS_MAX_MCP.md       <-- Plan de auditoría y PRs quirúrgicos para servidores MCP
├── skills/                           <-- Habilidades locales para agentes de IA
│   ├── maxpylang/                    <-- Generación programática de parches .maxpat y .amxd
│   ├── ersatzben-maxmsp-mcp/         <-- Reglas críticas de parcheo y tipos numéricos
│   ├── patch-guidelines/             <-- Nomenclatura, layout y scripting JS
│   ├── organize-patch/               <-- Algoritmos de ordenamiento visual
│   ├── max-techniques/               <-- poly~, bpatcher, pattrstorage
│   ├── m4l-techniques/               <-- Live Object Model para Ableton
│   ├── genexpr-dsp/                  <-- Sintaxis y optimización para gen~ [Pendiente]
│   ├── py2max-generator/             <-- Generación programática de parches con Python [Pendiente]
│   └── max-sdk-neural-audio/         <-- Inferencia LibTorch/RTNeural en C++ [Pendiente]
└── templates/                        <-- Plantillas CMake y esqueletos de externals C++
```

---
*Catálogo actualizado y estructurado para maximizar la robustez en el desarrollo de externals C++ y la automatización agéntica con IA en Max/MSP y Ableton Live.*
