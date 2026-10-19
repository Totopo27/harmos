#pragma once

#include <vector>
#include <cmath>
#include <algorithm>

namespace harmos {
namespace math {

/**
 * Aritmética modular euclidiana estricta para números enteros.
 * Garantiza resultados positivos en el rango [0, m-1].
 */
inline int mod_euclidean(int n, int m) {
    if (m == 0) return 0;
    return ((n % m) + m) % m;
}

struct InversionPair {
    int note_a;
    int note_b;
    bool is_fixed_point;
};

/**
 * Calcula los pares de inversión simétricos y puntos fijos para un temperamento igual (n-TET)
 * dada una suma de índices fija S.
 */
inline std::vector<InversionPair> get_inversion_pairs(int divisions, int index_sum) {
    std::vector<InversionPair> pairs;
    std::vector<bool> visited(divisions, false);

    for (int i = 0; i < divisions; ++i) {
        if (visited[i]) continue;

        int partner = mod_euclidean(index_sum - i, divisions);
        visited[i] = true;
        visited[partner] = true;

        InversionPair pair;
        pair.note_a = i;
        pair.note_b = partner;
        pair.is_fixed_point = (i == partner);
        pairs.push_back(pair);
    }

    return pairs;
}

/**
 * Calcula el factor de curvatura Bézier proporcional para unir dos notas en coordenadas polares.
 */
inline double calculate_bezier_curvature(int note_a, int note_b, int divisions) {
    int diff = std::abs(note_b - note_a);
    int angular_dist = std::min(diff, divisions - diff);
    double max_dist = divisions / 2.0;
    if (max_dist == 0.0) return 0.0;
    return (1.0 - (angular_dist / max_dist)) * 0.6;
}

} // namespace math
} // namespace harmos
