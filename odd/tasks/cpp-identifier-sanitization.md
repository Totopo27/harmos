# Saneo de identificadores C++ en el generador

Objetivo: que un nombre de atributo del IR (un `symbol` de Max, libre por contrato) nunca produzca un identificador C++ invalido, sin cambiar el nombre que el usuario ve en el Inspector.
Rama: `fix/cpp-identifier-sanitization` — Entrega: un work-unit commit — Runner: `python -m unittest discover tests`

## Specs

**S1.** Un atributo cuyo nombre no es un identificador C++ valido (`cut-off`) se emite como miembro saneado (`double cut_off{0.7};`) y el kernel generado compila. El kernel no contiene el nombre original.

**S2.** Un nombre que coincide con una keyword de C++ (`class`) recibe el sufijo determinista `_` (`double class_{1.0};`) y compila.

**S3.** El wrapper Min-Devkit conserva el nombre original como cadena de cara a Max (`attribute<float> cut_off { this, "cut-off", ...`) y escribe el setter sobre el identificador saneado (`m_kernel.cut_off = ...`).

**S4.** Dos atributos distintos que normalizan al mismo identificador son un `ValueError` explicito que nombra ambos originales; nunca se elige uno en silencio.

**S5.** El mismo saneo se aplica al nombre del objeto (`object_name`) que nombra la clase del kernel y el wrapper.

Alcance excluido: la coercion de atributos `string` a `double` en el kernel, y el mapeo de tipos IR (`color`, `symbol`) a tipos de Min-Devkit. Son defectos distintos del emisor.

## Tasks

| ID | Specs | Ruta | Estado |
| :--- | :--- | :--- | :--- |
| T1 | S1-S4 | inline | RED: `TestCppIdentifierSafety` (4 tests, incluye compilacion real con g++/clang++) |
| T2 | S1-S5 | inline | GREEN: `cpp_identifier` + `_attribute_identifiers` cableados en ambos generadores |
| T3 | S1-S5 | inline | verificacion: suite completa, `check.py`, e2e sobre IR real con `cut-off` y `class` |

## Log

**L1 (peticion original, verbatim):** "vamos con ello" — tras la recomendacion de la opcion A: sanear el identificador C++ en el generador y preservar el nombre original como simbolo de Max; colision tras normalizar = error explicito nombrando ambos originales; keyword C++ = sufijo `_` determinista.

**L2 (origen del hallazgo):** audit de `70084a0`. El generador copiaba `attributes[].name` sin mas a un identificador C++, y `core/schema/max_object_ir.schema.json` declara `name` como `{"type": "string"}` sin patron. Un IR con `cut-off` o `class` producia `double cut-off{...};` y no compilaba. Nada en CI compila el kernel generado.

**L3 (decision de capas):** el nombre de un atributo en Max es un `symbol` que el usuario ve; que C++ no acepte guiones es una restriccion de nuestra herramienta de implementacion, no del dominio. Endurecer el esquema filtraria esa restriccion al contrato publicado y romperia IRs ya consumidos. Se sanea el identificador y se preserva el nombre Max.

**L4 (verificacion):** suite completa `Ran 157 tests ... OK`; `scripts/check.py` PASS con escaneo de privacidad real. E2E: IR con `cut-off` (float) y `class` (int) compilado con el pipeline completo produce `test.cutoff_probe.mxe64`, procedencia `VALID` → kernel alterado → `STALE_ARTIFACTS` → restaurado → `VALID`.

**L5 (hallazgo abierto, no corregido aqui):** el IR del benchmark `benchmarks/teclados-wilson/wilson_hexslider_ir.json` no compila con el pipeline. `type: "color"` emite `attribute<color>` con default de lista (`[0.12, 0.12, 0.14, 1.0]`, que C++ parsea como lambda) y `type: "symbol"` con default `'edo'` emite `edo` sin comillas. Es el mapeo de tipos IR -> Min-Devkit, fuera del alcance de este work unit.
