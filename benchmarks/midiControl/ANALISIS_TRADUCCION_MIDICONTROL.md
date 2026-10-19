# Análisis Arquitectónico del Traductor: midiControl / midiOSCControl hacia Max MSP

> **Dictamen del Meta-Traductor**: Aplicación estricta del principio de **Zero Re-invention** y **Separation of Concerns**.

---

## 1. ¿Qué es midiControl bajo el capó?
Inspeccionando los módulos de referencia `bridge.js` y `processor.js`:
- Es un **enrutador y puente bidireccional** entre:
  1. Puertos MIDI físicos de hardware (USB-MIDI).
  2. Puertos MIDI virtuales (para comunicarse con DAWs como Ableton o Reaper).
  3. Paquetes UDP OSC (Open Sound Control para SuperCollider, Max o TouchOSC).
  4. Un motor de Hot-Plug Watchdog (reconexión automática si se desconecta el cable USB).

---

## 2. Auditoría contra el Catálogo Canónico de Max (`catalog/max_primitives.json`)

| Funcionalidad de midiControl | ¿Max ya lo tiene nativamente? | Objeto Canónico de Max | Recomendación Arquitectural |
| :--- | :---: | :--- | :--- |
| **Envío de paquetes OSC por red** | **SÍ** | `udpsend <host> <puerto>` | **Reutilizar nativo**. Max maneja UDP en C con latencia sub-milisegundo. |
| **Recepción de paquetes OSC** | **SÍ** | `udpreceive <puerto>` | **Reutilizar nativo**. |
| **Parsing y Bundling OSC** | **SÍ** | `OpenSoundControl`, `OSC-route` | **Reutilizar nativo**. |
| **I/O MIDI de Hardware y Virtual** | **SÍ** | `midiin`, `midiout`, `notein`, `noteout`, `ctlin`, `ctlout` | **Reutilizar nativo**. Max gestiona directamente la lista de dispositivos MIDI de Windows. |
| **Puertos Virtuales en Windows** | **SÍ** | "from Max 1", "to Max 1" | Max crea puertos virtuales internos en Windows automáticamente. |
| **Conversión MIDI a Mensaje OSC** | **PARCIAL** | Mapeo mediante subpatches / `sprintf` / `route` | Requiere cables tediosos si se quiere mapeo dinámico de namespaces. |
| **Mapeo Microtonal MPE (Multidimensional Polyphonic Expression)** | **NO NATIVO FÁCIL** | Requiere lógica para repartir notas en 15 canales con pitch-bend de 14 bits por nota | **Candidato a Objeto Especializado (`micro.mpe`)**. |

---

## 3. Estrategia de Portabilidad: ¿External en C++, Abstracción o Node for Max?

Si intentamos hacer un objeto C++ monolítico que abra puertos UDP y puertos MIDI dentro del external, **estaríamos duplicando el subsistema MIDI y de red que Max ya tiene perfeccionado**.

La arquitectura idiomática y profesional para llevar `midiControl` a Max es un **Tándem en dos capas**:

### Capa 1: El Puente de Control Microtonal (`wilson.mpe~` o `micro.mpe`) — C++ External
Un external ligero en C++ especializado que toma la salida de `wilson.hexslider`:
- **Entrada**: Frecuencia en Hz y Velocity de cada toque.
- **Lógica**: Convierte los Hz microtonales a:
  - Canal MIDI MPE rotativo (Canales 2 al 16).
  - Número de nota MIDI base más cercano.
  - Mensaje de Pitch-Bend de 14 bits exacto para la micro-desviación.
- **Salida**: Mensajes estándar listos para conectar a `midiformat` o sintetizadores MPE nativos de Max (como `retune~` o sintetizadores VST en Max).

### Capa 2: La Consola de Ruteo y Monitoreo OSC (`midicontrol.bridge`) — Max Abstraction / Node for Max
Un módulo (bpatcher) reutilizable de Max que:
- Empaqueta los datos del teclado a namespaces OSC limpios: `/wilson/note [hex_id, freq_hz, vel]`, `/wilson/tuning [edo_divisions, base_freq]`.
- Se conecta directo a `udpsend` para transmitir a Reaper, Ableton, TouchOSC o un iPad por Wi-Fi.
- Recibe comandos OSC remotos desde TouchOSC/iPad por `udpreceive` para gobernar el teclado a distancia.
