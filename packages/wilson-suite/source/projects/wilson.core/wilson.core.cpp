#include "c74_min.h"
#include <vector>
#include <algorithm>
#include <cmath>
#include <string>

using namespace c74::min;

/**
 * @brief wilson_core: Motor de cálculo armónico de Erv Wilson en C++ para Max MSP.
 * Extraído de la lógica pura de Teclados-Wilson (hexany-data.js).
 * Calcula combinatorias de factores primos, normaliza ratios a la octava [1.0, 2.0)
 * y emite frecuencias en Hz y cents para Max MSP.
 */
class wilson_core : public object<wilson_core> {
public:
    MIN_DESCRIPTION {"Motor de cálculo armónico de Erv Wilson (Hexany, CPS, Ratios)"};
    MIN_TAGS        {"microtonal, wilson, tuning, scales"};
    MIN_AUTHOR      {"OptimizandoParaMaxSDK"};
    MIN_RELATED     {"kslider, coll, dict, mtof"};

    // Inlets
    inlet<> input_inlet { this, "(list / symbol) Factores primos (ej. 1 3 5 7) o comandos" };

    // Outlets
    outlet<> ratios_outlet     { this, "(list) Ratios armónicos normalizados a la octava [1.0, 2.0)" };
    outlet<> frequencies_outlet{ this, "(list) Frecuencias resultantes en Hz" };
    outlet<> cents_outlet      { this, "(list) Desviaciones en cents respecto a la fundamental" };

    // Atributos de Inspector
    attribute<double> base_frequency { this, "base_freq", 261.625565, // C4 (Hz)
        description {"Frecuencia base en Hz de la nota fundamental 1/1"}
    };

    attribute<int> combination_k { this, "k", 2,
        description {"Tamaño de las combinaciones (k=2 para pares/Hexany, k=3 para tríadas/Eikosany)"}
    };

    // Constructor
    wilson_core(const atoms& args = {}) {
        if (!args.empty()) {
            set_factors(args);
        } else {
            // Factores por defecto para un Hexany clásico (1, 3, 5, 7)
            factors = { 1, 3, 5, 7 };
            recalculate();
        }
    }

    // Mensaje para recibir factores como lista
    message<threadcheck::none> list { this, "list", "Configura los factores primos y recalcula la escala",
        MIN_FUNCTION {
            set_factors(args);
            recalculate();
            return {};
        }
    };

    message<> bang { this, "bang", "Emite los valores calculados por los outlets",
        MIN_FUNCTION {
            emit_results();
            return {};
        }
    };

private:
    std::vector<int> factors;
    std::vector<double> computed_ratios;
    std::vector<double> computed_frequencies;
    std::vector<double> computed_cents;

    void set_factors(const atoms& args) {
        factors.clear();
        for (const auto& item : args) {
            if (item.type() == message_type::int_argument) {
                int f = static_cast<int>(item);
                if (f > 0) factors.push_back(f);
            }
        }
        if (factors.empty()) {
            factors = { 1, 3, 5, 7 };
        }
    }

    // Combinatoria sin repetición: C(n, k)
    void get_combinations(const std::vector<int>& arr, size_t k, size_t start, 
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

    // Normalizar ratio al rango [1.0, 2.0)
    double reduce_to_octave(double ratio) {
        if (ratio <= 0.0) return 1.0;
        while (ratio >= 2.0) ratio /= 2.0;
        while (ratio < 1.0)  ratio *= 2.0;
        return ratio;
    }

    void recalculate() {
        computed_ratios.clear();
        computed_frequencies.clear();
        computed_cents.clear();

        size_t k_val = static_cast<size_t>(combination_k.get());
        if (k_val == 0 || k_val > factors.size()) k_val = 2;

        std::vector<std::vector<int>> combos;
        std::vector<int> current;
        get_combinations(factors, k_val, 0, current, combos);

        // Multiplicar factores de cada combinación para obtener el producto de combinación (CPS)
        for (const auto& combo : combos) {
            double product = 1.0;
            for (int f : combo) {
                product *= static_cast<double>(f);
            }
            double norm_ratio = reduce_to_octave(product);
            computed_ratios.push_back(norm_ratio);
        }

        // Ordenar los ratios de menor a mayor para formar una escala ascendente
        std::sort(computed_ratios.begin(), computed_ratios.end());

        double base_hz = base_frequency.get();
        for (double r : computed_ratios) {
            computed_frequencies.push_back(base_hz * r);
            double cents = 1200.0 * std::log2(r);
            computed_cents.push_back(cents);
        }

        emit_results();
    }

    void emit_results() {
        atoms ratios_out;
        for (double r : computed_ratios) ratios_out.push_back(r);

        atoms freqs_out;
        for (double f : computed_frequencies) freqs_out.push_back(f);

        atoms cents_out;
        for (double c : computed_cents) cents_out.push_back(c);

        // Emitir de derecha a izquierda (convención idiomática de Max MSP)
        cents_outlet.send(cents_out);
        frequencies_outlet.send(freqs_out);
        ratios_outlet.send(ratios_out);
    }
};

MIN_EXTERNAL(wilson_core);
