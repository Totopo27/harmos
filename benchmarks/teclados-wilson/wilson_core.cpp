#include "c74_min.h"
#include "wilson_kernel.hpp"
#include <vector>

using namespace c74::min;

/**
 * @brief wilson_core: Wrapper Min-Devkit para el motor armónico de Erv Wilson en Max MSP.
 * 
 * Arquitectura desacoplada de Harmos:
 * Delega el cálculo matemático, combinatorias y afinaciones puras en
 * harmos::kernels::wilson::WilsonKernel (wilson_kernel.hpp).
 * wilson_core actúa únicamente como capa de enlace para inlets, outlets y atributos de Max.
 */
class wilson_core : public object<wilson_core> {
private:
    harmos::kernels::wilson::WilsonKernel m_kernel;

public:
    MIN_DESCRIPTION {"Motor de cálculo armónico de Erv Wilson (Hexany, CPS, Ratios) - Harmos Decoupled"};
    MIN_TAGS        {"microtonal, wilson, tuning, scales"};
    MIN_AUTHOR      {"OptimizandoParaMaxSDK"};
    MIN_RELATED     {"kslider, coll, dict, mtof"};

    // Inlets
    inlet<> input_inlet { this, "(list / symbol) Factores primos (ej. 1 3 5 7) o comandos" };

    // Outlets
    outlet<> ratios_outlet     { this, "(list) Ratios armónicos normalizados a la octava [1.0, 2.0)" };
    outlet<> frequencies_outlet{ this, "(list) Frecuencias resultantes en Hz" };
    outlet<> cents_outlet      { this, "(list) Desviaciones en cents respecto a la fundamental" };

    // Atributos de Inspector sincronizados con m_kernel
    attribute<double> base_frequency { this, "base_freq", 261.625565, // C4 (Hz)
        description {"Frecuencia base en Hz de la nota fundamental 1/1"},
        setter { MIN_FUNCTION {
            m_kernel.base_frequency = static_cast<double>(args[0]);
            m_kernel.recalculate();
            return args;
        }}
    };

    attribute<int> combination_k { this, "k", 2,
        description {"Tamaño de las combinaciones (k=2 para pares/Hexany, k=3 para tríadas/Eikosany)"},
        setter { MIN_FUNCTION {
            m_kernel.combination_k = static_cast<int>(args[0]);
            m_kernel.recalculate();
            return args;
        }}
    };

    // Constructor
    wilson_core(const atoms& args = {}) {
        if (!args.empty()) {
            set_factors(args);
        } else {
            m_kernel.set_factors({ 1, 3, 5, 7 });
        }
    }

    // Mensaje para recibir factores como lista
    message<threadcheck::none> list { this, "list", "Configura los factores primos y recalcula la escala",
        MIN_FUNCTION {
            set_factors(args);
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
    void set_factors(const atoms& args) {
        std::vector<int> f_list;
        for (const auto& item : args) {
            if (item.type() == message_type::int_argument) {
                int f = static_cast<int>(item);
                if (f > 0) f_list.push_back(f);
            }
        }
        m_kernel.set_factors(f_list);
        emit_results();
    }

    void emit_results() {
        atoms ratios_out;
        for (double r : m_kernel.computed_ratios) {
            ratios_out.push_back(r);
        }

        atoms freqs_out;
        for (double f : m_kernel.computed_frequencies) {
            freqs_out.push_back(f);
        }

        atoms cents_out;
        for (double c : m_kernel.computed_cents) {
            cents_out.push_back(c);
        }

        // Emitir de derecha a izquierda (convención idiomática de Max MSP)
        cents_outlet.send(cents_out);
        frequencies_outlet.send(freqs_out);
        ratios_outlet.send(ratios_out);
    }
};

MIN_EXTERNAL(wilson_core);
