# TET Inversion Geometry Reference

## Mathematical Foundations

For an equal temperament system with $T$ divisions per octave ($T \in [3, 72]$) and a fixed index sum $S \in [0, T-1]$:

### Modular Inversion Mapping

$$\text{partner}(i) = ((S - i) \pmod T + T) \pmod T$$

### Fixed Points vs Inversion Pairs

- **Fixed Point**: If $\text{partner}(i) == i$, pitch class $i$ is invariant under inversion and lies on the symmetry axis.
- **Inversion Pair**: If $\text{partner}(i) \neq i$, $[i, \text{partner}(i)]$ forms a bilateral inversion pair. Pairs must be recorded once (avoiding reversed duplicates).

### Parity Properties

- **Even $T$** (e.g. 12, 24, 72):
  - $S$ even: exactly 2 fixed points separated by $T/2$.
  - $S$ odd: 0 fixed points; symmetry axis bisects intervals.
- **Odd $T$** (e.g. 19, 31, 41, 53):
  - Any $S$: exactly 1 fixed point. The opposite side of the symmetry axis bisects an interval.

## Polar Coordinates and Bézier Arcs

Given a circle of radius $R$ centered at $(x_0, y_0)$:
- Angular position for note $i$: $\theta_i = \frac{2\pi i}{T} - \frac{\pi}{2}$
- Circle point: $(x_i, y_i) = (x_0 + R \cos\theta_i, y_0 + R \sin\theta_i)$
- Angular distance: $d = \min(|p - i|, T - |p - i|)$
- Curvature factor: $k = (1 - \frac{d}{T/2}) \times 0.6$
- Control point $(cx, cy)$ computed toward center $(x_0, y_0)$ proportional to $k$.
