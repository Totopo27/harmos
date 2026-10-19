# Investigación Arquitectónica: Estado del Arte de "OSC Piano Roll / DAW OSC Editor"

> **Hipótesis del Usuario**: En todos los DAWs existe un editor MIDI (Piano Roll) para componer y editar notas y automatizaciones de 7 bits. ¿Existe una versión equivalente nativa pensada directamente para **OSC (Open Sound Control)**? ¿Cómo lo aborda la industria y el open-source (Ardour, IanniX, Ossia Score)? ¿Cómo se diseña un editor de eventos OSC nativo?

---

## 1. El Vacío en la Industria: ¿Por qué los DAWs no tienen un "OSC Piano Roll"?

### El problema de raíz:
1. **MIDI tiene semántica musical cerrada**: El protocolo MIDI define qué es una nota: un `Note-On` tiene un número de 0 a 127 y una velocidad de 0 a 127. Por eso cualquier DAW (Reaper, Cubase, Ableton, Ardour) puede dibujar un piano con teclas blancas y negras de 12 semitonos.
2. **OSC es un protocolo de transporte tipado arbitrario**: OSC no define qué es una nota. Define paquetes binarios sobre UDP con un *Address Pattern* (ej. `/synth/cutoff`) y argumentos heterogéneos (`float32`, `int32`, `string`, `blob`, `double64`).
3. **Cómo usa Ardour el protocolo OSC**:
   - En **Ardour** (repositorio `https://github.com/ardour/ardour`), OSC está implementado como una **superficie de control bidireccional (Control Surface)** para faders, transporte, mutes y automatización de volumen (`/strip/fader`, `/transport/play`).
   - Ardour **no tiene un Piano Roll de OSC**. Sus pistas MIDI siguen grabando MIDI tradicional de 7 bits.

---

## 2. El Estado del Arte: Los Proyectos que Intentaron Resolverlo

Al investigar el ecosistema global de audio y música por computadora, existen 3 grandes referentes:

| Proyecto | Paradigma | ¿Cómo resuelve la edición temporal de OSC? | Limitación |
| :--- | :--- | :--- | :--- |
| **IanniX** (basado en Xenakis) | Secuenciador gráfico 2D/3D | Dispara mensajes OSC cuando cabezales de reproducción cruzan curvas y trayectorias espaciales. | No es un Piano Roll musical; es un entorno matemático abstracto. |
| **Ossia Score** (`ossia.io`) | Secuenciador interactivo multimedia | Permite crear pistas de automatización de OSC en una línea de tiempo y secuenciar curvas continuas hacia Max/Pd. | Aunque tiene piano roll MIDI, su edición de OSC es por curvas de automatización o scripts, no un piano roll de notas OSC. |
| **Vezér / TouchOSC** | Controladores y timeline | Automatizan parámetros OSC en el tiempo para visuales y shows en vivo. | Enfocados en parámetros continuos de iluminación/video, no en composición de notas musicales complejas. |

---

## 3. La Oportunidad Arquitectónica: El "OSC Note & Event Roll"

La idea que planteás es **revolucionaria y ataca exactamente la limitación del MIDI**:
En un **OSC Piano Roll**:
- El eje Y (vertical) **no está atado a 12 semitonos**: puede representar frecuencias continuas en Hz (0 a 20.000 Hz), cents microtonales, o ratios armónicos de Wilson/Partch.
- Cada "bloque de nota" no emite un par 0-127: emite un bundle OSC con resolución flotante de 64 bits:
  $$\text{Bundle}: \left[ /note/start, \text{ id}, \text{ freq\_hz}, \text{ velocity\_float}, \text{ duration\_ms}, \text{ timbre\_params} \dots \right]$$
- No hay compresión ni cuantización a 127 pasos; permite microtonalismo infinito y modulación polifónica continua por nota sin las restricciones de canales de MPE.

---

## 4. Estrategia de Diseño para el Ecosistema

Podemos estructurar esta idea como un proyecto hermano o módulo avanzado:
1. **Modelado del Objeto UI (`osc.pianoroll` en Max o Standalone)**:
   - Lienzo temporal 2D con zoom horizontal (tiempo/compases) y zoom vertical (frecuencia logarítmica Hz / notas microtonales).
   - Bloques arrastrables con soporte para micro-tuning.
2. **Motor de Serialización y Playback**:
   - Secuenciador que despacha paquetes UDP nativos de Max (`udpsend`) según el reloj de transporte (`transport`).
3. **Estudio del Core de Ardour**:
   - Analizar cómo Ardour implementa `libs/ardour/osc.cc` y el parser de timeline para adoptar sus estructuras de datos de tiempo real.
