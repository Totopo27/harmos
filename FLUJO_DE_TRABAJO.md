# Flujo de Trabajo: Pipeline de Compilación y Verificación de Harmos

> **Metodología**: Organic Driven Development (ODD), Arquitectura Hexagonal y Compuertas Binarias Estrictas (*Decision Gates*) con Oráculos Duales (Semántico Headless + Estructural en Vivo).

---

## 1. Mandatos Fundamentales

1. **CERO Hardcoding**: Queda estrictamente prohibido cablear puertos a ciegas o asumir números de inlets/outlets. Toda interconexión debe resolverse a través de `core/schema/max_contracts.json` o `ContractEngine`.
2. **Desacoplamiento Estricto de Dominio**: Harmos es un meta-compilador agnóstico. Las suites y benchmarks (Wilson, Truax, TET) son casos de estrés, no el núcleo del compilador (ADR-0001).
3. **Dual Oracle Verification**:
   - **Semántico**: Verificación matemática determinista de resultados numéricos mediante vectores de prueba (`cases.jsonl`).
   - **Estructural**: Verificación de instanciación, contratos y compatibilidad en vivo mediante la consola interna de Max MSP (`Max.log`).
4. **Fail-Closed & Honestidad Epistémica**: Si el entorno carece de compilador C++ o runtime de Max, el resultado debe reportarse categóricamente como `BLOCKED (*_UNAVAILABLE)`, nunca `PASS`.

---

## 2. Las 5 Compuertas de Verificación (5-Gate Pipeline)

```
[Insumo: Código Fuente (TS, SC, C++)]
               │
               ▼
[ Compuerta 1: Validación de IR y Contratos ]
  - Esquema: core/schema/max_object_ir.schema.json
  - Catálogo: core/schema/max_contracts.json
               │ (PASS)
               ▼
[ Compuerta 2: Síntesis Determinista ]
  - TypedPatch (.maxpat con cero cables ciegos)
  - cpp_generator (*_kernel.hpp puro + *.cpp Min wrapper)
  - maxref_generator (*.maxref.xml canónico)
  - provenance (emitted-from.json con SHA-256)
               │ (PASS)
               ▼
[ Compuerta 3: Oráculo Semántico Headless ]
  - cases.jsonl cosechado o sintético
  - cpp_headless_runner.py (evaluación C++17 autónoma en host)
  - Tolerancia escalar de coma flotante
               │ (PASS)
               ▼
[ Compuerta 4: Guardrail Pre-Commit (check.py) ]
  - Tests unitarios completos (100% PASS)
  - Validación de esquemas y contratos
  - Escaneo estricto de PII y rutas absolutas
               │ (PASS)
               ▼
[ Compuerta 5: Auditoría Estructural en Vivo (audit.py) ]
  - Ejecución en vivo sobre Max.exe
  - Captura y parsing de Max.log (0 errores, 0 warnings de tipo)
  - Emisión de veredicto final certificado
```

---

## 3. Matriz de Veredictos del Sistema

| Veredicto | Significado | Condición |
| :--- | :--- | :--- |
| **`PASS (ESTRUCTURAL)`** | Patcher certificado en vivo en Max. | 0 errores en `Max.log` tras despliegue real en `Max.exe`. |
| **`PASS (SEMANTIC)`** | Equivalencia numérica aprobada. | 100% de casos en `cases.jsonl` dentro de la tolerancia de coma flotante. |
| **`BLOCKED (RUNTIME_UNAVAILABLE)`** | Max no está instalado en el host. | `scripts/audit.py` no detecta `Max.exe` o `Max` en rutas estándar de Windows/macOS. |
| **`BLOCKED (COMPILER_UNAVAILABLE)`** | No hay compilador C++ en PATH. | `g++`, `clang++` y `cl` ausentes en el host para ejecutar el arnés headless. |
| **`STALE_CONTRACTS`** | Deriva de especificaciones canónicas. | Hash SHA-256 de `max_contracts.json` difiere del registrado en `emitted-from.json`. |
| **`STALE_IR` / `STALE_SOURCE`** | Modificación posterior a la emisión. | La IR o el código fuente cambiaron tras generar el paquete. |
| **`UNVERIFIABLE`** | Evidencia incompleta o ausente. | Falta archivo fuente, contrato o registro criptográfico para validar procedencia. |
| **`FAIL`** | Fallo técnico o discrepancia. | Error de compilación, excepción en tiempo de ejecución o divergencia numérica. |
