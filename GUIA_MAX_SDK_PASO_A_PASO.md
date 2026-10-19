# Guía Suprema de Optimización y Desarrollo para Max MSP SDK (C / C++)

> **Visión de Arquitectura**: Convertir código o algoritmos existentes a objetos nativos de Max/MSP (*externals*) requiere dominar tanto la cadena de herramientas en Windows como la disciplina de programación en tiempo real (DSP). Esta guía establece el estándar profesional para construir objetos robustos, eficientes y libres de glitcheos de audio.

---

## Índice
1. [Fase 1: Configuración de la Cadena de Herramientas (Windows)](#fase-1-configuración-de-la-cadena-de-herramientas-windows)
2. [Fase 2: Estructura del SDK y Paquetes de Max](#fase-2-estructura-del-sdk-y-paquetes-de-max)
3. [Fase 3: Paradigmas — C API Clásico (`max-sdk-base`) vs. Modern C++ (`min-devkit`)](#fase-3-paradigmas--c-api-clásico-max-sdk-base-vs-modern-c-min-devkit)
4. [Fase 4: Optimización Extrema y Reglas de Tiempo Real (Audio DSP & Threading)](#fase-4-optimización-extrema-y-reglas-de-tiempo-real-audio-dsp--threading)
5. [Fase 5: Estrategia de Portabilidad desde JavaScript, TypeScript y Python a C/C++](#fase-5-estrategia-de-portabilidad-desde-javascript-typescript-y-python-a-cc)
6. [Fase 6: Integración e Interoperabilidad (Dictionaries, JS, Node for Max)](#fase-6-integración-e-interoperabilidad-dictionaries-js-node-for-max)
7. [Fase 7: Compilación, Hot-Reload y Depuración en Vivo con Visual Studio](#fase-7-compilación-hot-reload-y-depuración-en-vivo-con-visual-studio)
8. [Recursos de Documentación Extendida](#recursos-de-documentación-extendida)

---

## Fase 1: Configuración de la Cadena de Herramientas (Windows)

Para compilar binarios de 64 bits nativos (`.mxe64`) compatibles con la ABI (Application Binary Interface) de `Max.exe` en Windows, se requiere la herramienta oficial de Microsoft (MSVC).

### 1. Requisitos de Software
* **Visual Studio 2022** (Community, Professional o Enterprise).
  * **Carga de trabajo obligatoria**: *Desarrollo para el escritorio con C++* (*Desktop development with C++*).
  * **Componentes opcionales clave**:
    * `Herramientas de C++ para CMake en Windows` (*C++ CMake tools for Windows*).
    * `SDK de Windows 10 o 11` (última versión instalada).
    * `MSVC v143 - Herramientas de generación de C++ para x64/x86`.
* **CMake**: Versión `>= 3.25` (viene integrado en Visual Studio o se puede instalar independientemente).
* **Git**: Necesario para clonar repositorios con submódulos recursivos.
* **Max 8 o Max 9**: Instalado en la ruta por defecto:
  * `C:\Program Files\Cycling '74\Max 8` (o `Max 9`).

---

## Fase 2: Estructura del SDK y Paquetes de Max

El truco fundamental para trabajar cómodo en Max es colocar tus proyectos dentro del directorio de **Packages** del usuario. De esta forma, cada compilación deposita el binario `.mxe64` directamente donde Max lo encuentra en tiempo de ejecución, sin tener que configurar variables de entorno globales.

### Ruta del Paquete del Usuario:
```text
C:\Users\<TuUsuario>\Documents\Max 8\Packages\mi-libreria-externals\
```

### Árbol de Proyecto Recomendado:
```text
mi-libreria-externals/
├── CMakeLists.txt              <-- CMake principal del paquete
├── c74support/                 <-- Submódulo de max-sdk-base o min-devkit
├── externals/                  <-- Destino de los binarios .mxe64
├── help/                       <-- Archivos de ayuda .maxhelp
├── patchers/                   <-- Abstracciones complementarias
└── source/
    └── projects/
        ├── mi_filtro_dsp/
        │   ├── CMakeLists.txt
        │   └── mi_filtro_dsp.cpp
        └── mi_objeto_control/
            ├── CMakeLists.txt
            └── mi_objeto_control.c
```

---

## Fase 3: Paradigmas — C API Clásico (`max-sdk-base`) vs. Modern C++ (`min-devkit`)

Cycling '74 ofrece dos vías para construir externals. La elección depende de la naturaleza de tu código fuente original.

| Característica | Classic C API (`max-sdk-base`) | Modern C++ (`min-devkit`) |
| :--- | :--- | :--- |
| **Lenguaje** | C (C99 / C11) o C++ clásico | Modern C++ (C++17 / C++20) |
| **Estilo de Código** | Funcional, macros de Max, structs explícitas | Orientado a Objetos, templates, sintaxis declarativa |
| **Gestión de Entradas/Salidas** | Inlets/Outlets manuales (`inlet_new`, `outlet_new`) | Miembros de clase declarativos (`inlet<>`, `outlet<>`) |
| **Concurrencia FIFO** | Manual (`t_fifo` o ringbuffers propios) | Integrado de serie (`min::fifo`) |
| **Sobrecarga de Abstracción** | Cero (contacto directo con el runtime C) | Mínima (desenrollado por plantilla en tiempo de compilación) |
| **Recomendado para** | Código legacy C, wrappers de librerías en C puro | Algoritmos C++ modernos, síntesis modular, lógica compleja |

---

## Fase 4: Optimización Extrema y Reglas de Tiempo Real (Audio DSP & Threading)

### 1. El Modelo de Hilos en Max
Max ejecuta bajo 3 contextos de hilos principales:
1. **Main Thread (GUI/UI Thread)**: Maneja la interfaz de usuario, eventos de ratón, apertura de archivos e impresión en la ventana de Max (`post`).
2. **Scheduler Thread (High Priority Timer)**: Procesa eventos MIDI, `metro` y temporizadores de alta precisión.
3. **Audio Thread (DSP Vector Processing)**: Procesa bloques de muestras de audio (*vectors*) con prioridad en tiempo real.

### 2. Las 3 Reglas de Oro del Audio Thread (Rutina `perform`)
1. **NUNCA allocar o liberar memoria**: Nada de `malloc`, `free`, `new`, `delete`, ni operaciones con contenedores dinámicos (`std::vector::push_back`). Todo espacio debe estar pre-asignado durante la inicialización (`dsp64`).
2. **NUNCA bloquear el hilo con Mutex**: Prohibido usar `std::mutex::lock()` o `critical_enter()`. La comunicación entre el Main Thread y el Audio Thread debe ser **lock-free** utilizando buffers circulares atómicos (`min::fifo` o `std::atomic`).
3. **NUNCA llamar a la GUI o consola directamente**: Para notificar eventos desde el Audio Thread a la UI, usá `defer()` o `schedule()`.

### 3. Evitar el Colapso por Números Denormales (FTZ/DAZ)
```cpp
#include <xmmintrin.h>
#include <pmmintrin.h>

// Activar Flush-To-Zero y Denormals-Are-Zero en el DSP perform routine
void enable_fast_math_denormals() {
    _mm_setcsr(_mm_getcsr() | 0x8040); // FTZ: bit 15, DAZ: bit 6
}
```

---

## Fase 5: Estrategia de Portabilidad desde JavaScript, TypeScript y Python a C/C++

Tener código o prototipos en **JavaScript, TypeScript o Python** influye directamente en cómo encaramos la portabilidad hacia C/C++.

### 1. ¿Por qué portar código de JS/TS/Python a C/C++?
* **Audio en Tiempo Real**: JavaScript (`js` u objetos de Node) y Python se ejecutan en el hilo principal (Main Thread) o en procesos secundarios asincrónicos. **NO pueden procesar bloques de audio en tiempo real** dentro del Audio Thread. Para síntesis, filtros o efectos DSP, es obligatorio portar el algoritmo a C/C++.
* **Rendimiento C++ vs Interpretes**: Para cálculo matricial, DSP o lógica con bucles pesados, el código C/C++ compilado es entre 10x y 100x más rápido que JS/Python.

### 2. Equivalencias de Tipos de Datos y Estructuras

| Concepto en JS / TS / Python | Equivalente en Max SDK C/C++ | Estrategia de Migración |
| :--- | :--- | :--- |
| `Array` / `list` | `t_atom*` array o `std::vector` | Extraer números con `atom_getfloat()` o símbolos con `atom_getsym()`. Pre-allocar el vector en C++. |
| `Object` / `{ key: val }` / `dict` | `t_dictionary` | Usar la API de Diccionarios de Max (`dictionary_getsym`, `dictionary_getlong`, `dictobj`). |
| `async` / `Promise` / Callbacks | `defer_low()` / `schedule()` | Mover eventos asincrónicos fuera del hilo de audio hacia el Main Thread. |
| Métodos de Array (`map`, `filter`) | Bucles `for` vectorizados C++ | Reemplazar métodos funcionales por bucles directos optimizables con AVX2. |

---

## Fase 6: Integración e Interoperabilidad (Dictionaries, JS, Node for Max)

Si querés conservar parte de tu infraestructura en JS/TS/Python (por ejemplo, llamadas a APIs web, parseo de JSON o interfaces de usuario) e interactuar con tu external de C++, la mejor forma es usando **Diccionarios de Max (`t_dictionary`)**:

### Lectura de Diccionarios enviados desde JS / Max en C++:
```cpp
#include "ext.h"
#include "ext_obex.h"
#include "ext_dictobj.h"

void recibir_diccionario_desde_js(t_object* x, t_symbol* s) {
    // Buscar diccionario registrado en el gestor de Max por su nombre de símbolo
    t_dictionary* d = dictobj_findregistered_retain(s);
    if (!d) return;

    t_atom_long valor = 0;
    dictionary_getlong(d, gensym("frecuencia"), &valor);

    object_post(x, "Parámetro recibido desde JS: %ld Hz", (long)valor);

    dictobj_release(d); // Liberar retención
}
```

---

## Fase 7: Compilación, Hot-Reload y Depuración en Vivo con Visual Studio

```powershell
# 1. Crear directorio de build
mkdir build
cd build

# 2. Generar solución de Visual Studio 2022 para 64 bits
cmake -G "Visual Studio 17 2022" -A x64 ..

# 3. Compilar en configuración Release
cmake --build . --config Release
```

---

## Recursos de Documentación Extendida

- **Documentación Oficial del Max SDK 8.2.0**: [https://sdk.cdn.cycling74.com/max-sdk-8.2.0/index.html](https://sdk.cdn.cycling74.com/max-sdk-8.2.0/index.html)
- **API JGraphics (Objetos de Interfaz Gráfica C)**: [https://sdk.cdn.cycling74.com/max-sdk-8.2.0/group__jgraphics.html](https://sdk.cdn.cycling74.com/max-sdk-8.2.0/group__jgraphics.html)
- **Repositorio Oficial Cycling74 max-sdk**: [https://github.com/Cycling74/max-sdk](https://github.com/Cycling74/max-sdk)
- **Framework Min-DevKit (Modern C++17)**: [https://github.com/Cycling74/min-devkit](https://github.com/Cycling74/min-devkit)
- **Node for Max (JavaScript & TypeScript en Max)**: [https://docs.cycling74.com/max8/vignettes/nodeformax_topic](https://docs.cycling74.com/max8/vignettes/nodeformax_topic)
