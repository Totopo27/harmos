#pragma once
/**
 * @file wilson_kernel.hpp
 * @brief Kernel C++ estándar puro para el motor armónico de Erv Wilson.
 * 
 * 100% desacoplado de la API de Cycling '74 Max SDK y Min-Devkit.
 * Permite compilación nativa en CI sin dependencias de Max.
 */
#include <vector>
#include <cmath>
#include <algorithm>
#include <cstddef>

namespace harmos::kernels::wilson {

class WilsonKernel {
public:
    double base_frequency { 261.625565 }; // C4 en Hz
    int combination_k { 2 };              // k=2 para pares (Hexany), k=3 para tríadas (Eikosany)
    std::vector<int> factors { 1, 3, 5, 7 };

    std::vector<double> computed_ratios;
    std::vector<double> computed_frequencies;
    std::vector<double> computed_cents;

    WilsonKernel() {
        recalculate();
    }

    void set_factors(const std::vector<int>& new_factors) {
        factors.clear();
        for (int f : new_factors) {
            if (f > 0) factors.push_back(f);
        }
        if (factors.empty()) {
            factors = { 1, 3, 5, 7 };
        }
        recalculate();
    }

    // Normalizar ratio al rango de octava [1.0, 2.0)
    static double reduce_to_octave(double ratio) noexcept {
        if (ratio <= 0.0) return 1.0;
        while (ratio >= 2.0) ratio /= 2.0;
        while (ratio < 1.0)  ratio *= 2.0;
        return ratio;
    }

    // Combinatoria sin repetición: C(n, k)
    static void get_combinations(const std::vector<int>& arr, size_t k, size_t start,
                                 std::vector<int>& current, std::vector<std::vector<int>>& result) {
        if (current.size() == k) {
            result.push_back(current);
            return;
        }
        for (size_t i = start; i < arr.size(); ++i) {
            current.push_back(arr[i]);
            get_combinations(arr, k, i + 1, current, result);
            current.pop_back();
        }
    }

    void recalculate() {
        computed_ratios.clear();
        computed_frequencies.clear();
        computed_cents.clear();

        size_t k_val = static_cast<size_t>(combination_k);
        if (k_val == 0 || k_val > factors.size()) {
            k_val = 2;
        }

        std::vector<std::vector<int>> combos;
        std::vector<int> current;
        get_combinations(factors, k_val, 0, current, combos);

        // Multiplicar factores de cada combinación para obtener el producto de combinación (CPS)
        for (const auto& combo : combos) {
            double product = 1.0;
            for (int f : combo) {
                product *= static_cast<double>(f);
            }
            computed_ratios.push_back(reduce_to_octave(product));
        }

        // Ordenar los ratios ascendentemente
        std::sort(computed_ratios.begin(), computed_ratios.end());

        // Calcular frecuencias en Hz y cents respecto a la fundamental
        for (double r : computed_ratios) {
            computed_frequencies.push_back(base_frequency * r);
            double cents = (r > 0.0) ? (1200.0 * std::log2(r)) : 0.0;
            computed_cents.push_back(cents);
        }
    }
};

} // namespace harmos::kernels::wilson
