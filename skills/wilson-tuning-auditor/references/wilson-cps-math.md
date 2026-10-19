# Wilson Tuning Mathematics Reference

## Combination Product Sets (CPS)

Erv Wilson developed Combination Product Sets as a method for generating harmonic structures from products of harmonic factors (typically odd primes: 1, 3, 5, 7, 9, 11).

### Common Structures

- **Hexany**: 4 factors chosen 2 at a time. Total notes: $\binom{4}{2} = 6$.
  - Factors: $A, B, C, D$
  - Products: $AB, AC, AD, BC, BD, CD$
- **Eikosany**: 6 factors chosen 3 at a time. Total notes: $\binom{6}{3} = 20$.
  - Factors: $A, B, C, D, E, F$
  - Products: Triads formed by all combinations of 3 factors.
- **Heptany / Dekany / Monany**: Higher or lower order subsets defined by Wilson's geometric projections.

## Octave Reduction Formula

Every raw product ratio $R$ must be reduced to the fundamental octave $[1.0, 2.0)$:

$$\text{ratio\_norm} = R \times 2^{-\lfloor \log_2(R) \rfloor}$$

## Cents Calculation

$$\text{cents} = 1200 \times \log_2(\text{ratio\_norm})$$

## Frequency and Pitch-Bend Mapping

- **Frequency (Hz)**: $f = f_0 \times \text{ratio\_norm}$, where $f_0$ is the base tuning reference (e.g., 440.0 Hz).
- **MPE Pitch Bend**: Deviation in cents mapped to 14-bit pitch bend range:
  $$\text{pb} = 8192 + \left\lfloor \frac{\text{deviation\_cents}}{\text{bend\_range\_cents}} \times 8192 \right\rfloor$$
