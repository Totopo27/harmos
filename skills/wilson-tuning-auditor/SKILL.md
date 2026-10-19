---
name: wilson-tuning-auditor
description: "Trigger: wilson-tuning, validar escalas wilson, hexany, eikosany, ratios. Valida y audita matemática de afinación microtonal de Wilson para Max MSP."
license: Apache-2.0
metadata:
  author: "OptimizandoParaMaxSDK"
  version: "1.1"
---

# Wilson Tuning Auditor

## Activation Contract

Cargar al implementar, auditar o traducir objetos de Max MSP basados en teorías de afinación de Erv Wilson (Hexany, Eikosany, Combination Product Sets - CPS, o EDOs 31, 41, 53).

## Hard Rules

- **Precisión Doble Obligatoria**: Calcular todo ratio armónico con precisión de 64 bits (`double`) antes de emitir a Max.
- **Normalización a la Octava**: Reducir estrictamente todo ratio $R$ al rango $[1.0, 2.0)$ mediante $\text{ratio\_norm} = R \times 2^{-\lfloor \log_2(R) \rfloor}$.
- **Cero Alojamientos en Hilos Críticos**: Precalcular tablas de afinación en el constructor o en el hilo Scheduler/Main; prohibido alojar memoria en bucles de audio DSP.
- **Cálculo Determinista de Cents**: Obtener cents mediante $\text{cents} = 1200 \times \log_2(\text{ratio\_norm})$.

## Decision Gates

| Estructura Armónica | Factores Base | Cantidad de Notas Generadas |
| :--- | :--- | :--- |
| **Hexany** | 4 factores tomando pares | $\binom{4}{2} = 6$ notas |
| **Eikosany** | 6 factores tomando tríadas | $\binom{6}{3} = 20$ notas |
| **Heptany / Monany** | Subconjuntos según diseño Wilson | Notas según configuración de factores |

## Execution Steps

1. Auditar factores primos de entrada verificando enteros positivos impares (ej. 1, 3, 5, 7, 9, 11).
2. Generar combinatoria sin repetición de los factores seleccionados.
3. Normalizar cada producto al intervalo $[1.0, 2.0)$ aplicando potencias de 2.
4. Calcular cents y convertir a frecuencias absolutas (Hz) o desviaciones de pitch-bend MPE.
5. Formatear la salida como lista de átomos de Max (`t_atom` en C++) o mensajes validados.

## Output Contract

- Veredicto binario de validación (PASS / FAIL) confrontado contra tablas canónicas de Wilson.
- Matriz de ratios normalizados, cents calculados y lista estructurada de átomos para Max.

## References

- `references/wilson-cps-math.md` — Fundamentos matemáticos de CPS, normalización de octava y mapeo MPE.
