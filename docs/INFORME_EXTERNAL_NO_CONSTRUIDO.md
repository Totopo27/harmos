# Diagnóstico: el patcher generado referencia un external no construido

Fecha: 2026-11-20  
Base inspeccionada: `c948140`  
Estado: resuelto y verificado con Live Runtime Audit PASS en Max 9.

## Resumen

El flujo probado genera fuentes C++, un kernel, un `CMakeLists.txt`, un patcher
de prueba y su registro de procedencia, pero no genera el external nativo.
Al abrir ese patcher, Max no encuentra el objeto personalizado y el auditor
devuelve `FAIL`. Una procedencia `VALID` no demuestra que exista un binario
cargable ni que el objeto funcione.

La causa inmediata está demostrada para esta reproducción: se abre un patcher
que referencia `harmos_repro_external` sin haber construido su external.
Todavía no se ha demostrado que el CMake generado sea suficiente para construirlo,
ni se ha verificado la cadena completa de SDK, compilador y búsqueda de Max.

## Alcance solicitado

El usuario eligió abordar el punto 1 del diagnóstico anterior: cerrar la brecha
entre la generación del paquete y la carga de su objeto en Max.

No se autoriza resolverlo sustituyendo el objeto por uno integrado, eliminándolo
del patcher o debilitando el auditor. Tampoco se han instalado herramientas,
descargado SDK ni modificado configuraciones globales de Max.

## Evidencia observada

| Comprobación | Resultado |
| --- | --- |
| Generación mediante `compile_ir` | Se emitieron los cinco archivos indicados abajo. |
| External nativo en el directorio generado | No se encontró ningún `.mxe64` ni `.mxo`. |
| Auditoría en Max real | `HARMOS LIVE AUDIT: FAIL`. |
| Mensaje específico de Max | `harmos_repro_external: No such object`. |
| Código de salida del auditor | `1`. |
| Procedencia | El auditor informó que la procedencia estaba verificada. |

Archivos observados:

```text
CMakeLists.txt
emitted-from.json
harmos_repro_external.cpp
harmos_repro_external_kernel.hpp
harmos_repro_external_test.maxpat
```

En Windows, el external esperado es `.mxe64`; `.mxo` corresponde a macOS.
La referencia anterior a construir un `.mxo` en este equipo era incorrecta.

### Localizadores en el código

- `core/compiler/cli.py:60-64`: `generate_cmakelists` emite únicamente
  `c74_min_project(<nombre>)`.
- `core/compiler/cli.py:67-97`: el patcher de prueba contiene el objeto
  personalizado indicado por el IR.
- `core/compiler/cli.py:100-137`: `compile_ir` genera los archivos y la
  procedencia, pero no ejecuta una construcción nativa.
- `core/compiler/cli.py:175`: la CLI imprime `Compilacion exitosa`, aunque
  este flujo no haya producido un external nativo.
- `scripts/audit.py:332`: se comprueba la procedencia antes del lanzamiento.
- `scripts/audit.py:349`: se lanza Max con el patcher.
- `scripts/audit.py:391-398`: se evalúa el log y se agrega el detalle de procedencia.

Los números de línea corresponden a la base inspeccionada.

## Reproducción mínima

Crear este IR en un directorio temporal externo al repositorio:

```json
{
  "object_name": "harmos_repro_external",
  "category": "control",
  "inlets": [],
  "outlets": []
}
```

Generar el paquete y auditar el patcher:

```text
python -m core.compiler.cli compile <scratch>/repro.ir.json --out <scratch>/pkg
python scripts/audit.py --patcher <scratch>/pkg/harmos_repro_external_test.maxpat --timeout 15
```

La ejecución observada utilizó `compile_ir` directamente para la primera etapa
y el comando público `scripts/audit.py` para la segunda. Las rutas anteriores
son marcadores, no rutas que deban copiarse literalmente.

Fragmento relevante del resultado:

```text
HARMOS LIVE AUDIT: FAIL
harmos_repro_external: No such object
Procedencia verificada: emitted-from.json certifica los contratos y la integridad de los artefactos emitidos.
AUDIT_EXIT=1
NATIVE_BINARIES=[]
```

La prueba no usa conexiones ni índices de inlets/outlets: el fallo se reproduce
con la mera presencia del objeto.

## Qué está demostrado y qué falta

**Demostrado:** el flujo probado no construye el binario y el patcher resultante
no carga correctamente en Max. El auditor rechaza esa carga; no debe convertirse
ese rechazo en un `PASS`.

**No demostrado:** que emitir fuentes sin construirlas sea, por sí solo, un
incumplimiento del contrato original del compilador. Su descripción actual habla
de generar esqueletos C++. Debe distinguirse generación de fuentes, construcción
nativa y verificación en runtime al definir la corrección.

Confirmado en una segunda ronda de inspección:

1. **Falta la etapa de construcción.** `compile_ir` no invoca ningún proceso de
   build (`core/compiler/cli.py:100-137`).
2. **El `CMakeLists.txt` emitido es inservible con el SDK local.** Emite
   únicamente `c74_min_project(<nombre>)` (`core/compiler/cli.py:60-64`), y esa
   función no existe en el Min-DevKit instalado. La búsqueda en
   `c74support/min-devkit/source/min-api/script/` devuelve solo
   `min-package.cmake`, `min-posttarget.cmake` y `min-pretarget.cmake`; la
   referencia canónica es `min.hello-world/CMakeLists.txt`, que incluye
   `min-pretarget.cmake`, declara `add_library(... MODULE ...)` y luego incluye
   `min-posttarget.cmake`. El sufijo `.mxe64` lo impone ese posttarget.
3. **No hay compilador C++ de MSVC instalado en este equipo.** Detalle abajo.

Todavía no se ha verificado si, una vez construido el external, Max lo resuelve
colocándolo junto al patcher. Esa comprobación requiere el toolchain y queda
pendiente.

## Bloqueador actual: toolchain

| Componente | Estado observado |
| --- | --- |
| `cmake` | Presente en `%USERPROFILE%\mingw64\bin\cmake.exe` |
| `ninja` | Presente en `%USERPROFILE%\mingw64\bin\ninja.exe` |
| Min-DevKit | Presente en `c74support/min-devkit` |
| `MaxAPI.lib`, `MaxAudio.lib`, `jitlib.lib` | Presentes en `max-sdk-base` |
| Binarios `.mxe64` previos | Presentes (`wilson.core.mxe64`, `micro.mpe.mxe64`, entre otros) |
| **Compilador MSVC (`cl.exe`)** | **Ausente inicialmente; instalado después** |

Evidencia del bloqueador inicial:

- `vswhere -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64` no
  devolvía ninguna instalación.
- `%ProgramFiles%\Microsoft Visual Studio\18\Community\VC` contenía solo
  `Auxiliary` y `Redist`; no existía el directorio `Tools\MSVC`.
- Una búsqueda de `cl.exe` en las raíces de Visual Studio no devolvía resultados.
- `c74support/min-devkit/build/CMakeCache.txt` registraba como linker
  `%ProgramFiles(x86)%/Microsoft Visual Studio/2022/BuildTools/VC/Tools/MSVC/14.44.35207/bin/Hostx64/x64/link.exe`,
  y ese directorio ya no existía en ese momento.

Los `.mxe64` existentes demuestran que la cadena funcionó en este equipo en el
pasado. El bloqueo es de entorno, no de diseño del proyecto.

MinGW (`gcc`, `clang` de llvm-mingw) no es una alternativa válida: el SDK de Max
distribuye bibliotecas de importación de MSVC y el external resultante debe ser
un binario compatible con el ABI con el que Max 9 carga `.mxe64`. Se deja fuera
de alcance cualquier intento de enlazar el SDK con MinGW.

Sin `cl.exe` no existe bucle de realimentación posible: no se puede construir el
external, y por tanto la auditoría en vivo no puede pasar de
`FAIL`/`BLOCKED`. Implementar la etapa de construcción sin poder ejecutarla
produciría código nunca ejecutado, que es exactamente lo que las reglas del
repositorio prohíben certificar.

## Próximo paso recomendado

1. Restituir el compilador MSVC (Visual Studio Build Tools con la carga de
   trabajo "Desarrollo para el escritorio con C++", componente
   `Microsoft.VisualStudio.Component.VC.Tools.x86.x64`). Sin esto no hay
   verificación posible.
2. Corregir `generate_cmakelists` para que emita la estructura real del
   Min-DevKit (pretarget, `add_library MODULE`, posttarget), con
   `C74_LIBRARY_OUTPUT_DIRECTORY` apuntando junto al patcher generado.
3. Añadir la invocación de configure y build, con resolución explícita del
   Min-DevKit (argumento o variable de entorno, nunca ruta de host embebida) y un
   fallo claro y accionable cuando falte cualquier herramienta.
4. Preservar el comportamiento actual (solo fuentes) mediante una opción
   explícita de emisión sin build.
5. Observar una prueba de regresión fallida antes de implementar, construir el
   external real y verificar su carga con
   `python scripts/audit.py --patcher <patcher_generado>`.
6. Ejecutar `python scripts/check.py` y registrar los resultados reales.

La corrección no puede certificarse por inspección estática ni solo mediante
mocks. Si falta el toolchain, el estado debe informarse como bloqueado por
entorno de construcción, sin inventar un binario ni un resultado favorable.

## Estado de entrega

Este informe documentó inicialmente el diagnóstico y el bloqueo de toolchain.
Tras la instalación de Visual Studio Build Tools 2022 (MSVC v143, x64):

1. Se implementó la plantilla CMake funcional en `core/compiler/cli.py` (`min-pretarget.cmake`, `add_library MODULE`, `min-posttarget.cmake` y enlace de librerías del SDK de Max).
2. Se conectó la etapa de construcción nativa `build_external` en `compile_ir` y la CLI (`--no-build` para solo fuentes).
3. Se corrigió la signatura de `message<>` en `core/compiler/cpp_generator.py`.
4. Se incorporó la prueba de regresión en `tests/test_cli.py`.
5. Se certificó en Max 9 real con `scripts/audit.py`, obteniendo `HARMOS LIVE AUDIT: PASS` con procedencia verificada.

Referencia de construcción del proveedor:
[Min-DevKit — ReadMe](https://github.com/Cycling74/min-devkit/blob/main/ReadMe.md).
