#include "c74_min.h"
#include "harmos_tet_math.hpp"
#include <vector>
#include <cmath>
#include <unordered_set>
#include <string>
#include <fstream>

using namespace c74::min;
using namespace c74::min::ui;

/**
 * @brief tet_circle: Objeto UI vectorial nativo de Max MSP para análisis de simetrías n-TET (3 a 72).
 * Implementado sobre C++ Min-Devkit / JGraphics.
 */
class tet_circle : public object<tet_circle>, public ui_operator<tet_circle> {
public:
    MIN_DESCRIPTION {"Generador vectorial nativo de círculos TET y análisis de simetrías de inversión"};
    MIN_TAGS        {"ui, microtonal, tet, inversion, symmetry, vector"};
    MIN_AUTHOR      {"OptimizandoParaMaxSDK"};
    MIN_RELATED     {"nodes, kslider, jsui"};

    // Inlets
    inlet<> input_inlet { this, "(int) Suma de índices S o bang", "anything" };
    inlet<> divs_inlet  { this, "(int) Divisiones n-TET (3 a 72)", "int" };

    // Outlets
    outlet<> pairs_outlet    { this, "(list) Pares de inversión [i, partner, ...]", "list" };
    outlet<> fixed_outlet    { this, "(list) Puntos fijos (ejes de simetría)", "list" };
    outlet<> count_outlet    { this, "(int) Cantidad de pares de simetría", "int" };
    outlet<> notify_outlet   { this, "(symbol) Notificación de exportación SVG", "symbol" };

    // Atributos de Inspector
    attribute<int> divisions { this, "divisions", 19,
        description {"Número de divisiones por octava (3 a 72)"},
        range { 3, 72 }
    };

    attribute<int> index_sum { this, "index_sum", 0,
        description {"Suma de índices para la inversión"},
        range { 0, 71 }
    };

    attribute<bool> show_inversion { this, "show_inversion", true,
        description {"Mostrar mapeo de curvas Bézier y puntos fijos"}
    };

    // Constructor
    tet_circle(const atoms& args = {}) {
    }

    // Aritmética modular euclidiana
    static int mod_euclid(int n, int m) {
        return ((n % m) + m) % m;
    }

    // Mensaje int
    message<threadcheck::none> int_msg { this, "int", "Recibe valores numéricos en los inlets",
        MIN_FUNCTION {
            if (inlet == 0) {
                index_sum = std::clamp(static_cast<int>(args[0]), 0, static_cast<int>(divisions) - 1);
                bang({});
            } else if (inlet == 1) {
                divisions = std::clamp(static_cast<int>(args[0]), 3, 72);
                index_sum = std::min(static_cast<int>(index_sum), static_cast<int>(divisions) - 1);
                bang({});
            }
            redraw();
            return {};
        }
    };

    // Mensaje bang para calcular y emitir consumiendo harmos::math
    message<threadcheck::none> bang { this, "bang", "Calcula y emite los pares y puntos fijos",
        MIN_FUNCTION {
            int divs = divisions;
            int sum = index_sum;

            auto calculated_pairs = harmos::math::get_inversion_pairs(divs, sum);

            atoms flat_pairs;
            atoms fixed_atoms;
            int pair_count = 0;

            for (const auto& p : calculated_pairs) {
                if (p.is_fixed_point) {
                    fixed_atoms.push_back(p.note_a);
                } else {
                    flat_pairs.push_back(p.note_a);
                    flat_pairs.push_back(p.note_b);
                    pair_count++;
                }
            }

            count_outlet.send(pair_count);
            fixed_outlet.send(fixed_atoms);
            pairs_outlet.send(flat_pairs);

            redraw();
            return {};
        }
    };

    // Renderizado JGraphics
    message<threadcheck::none> paint { this, "paint", "Dibuja el círculo vectorial en el patcher",
        MIN_FUNCTION {
            target<surface> t { args };
            auto w = t.width();
            auto h = t.height();
            double center_x = w / 2.0;
            double center_y = h / 2.0;
            double min_dim = std::min(w, h);
            double circle_radius = min_dim * 0.36;

            // Fondo
            t.set_source_rgba({0.12, 0.12, 0.14, 1.0});
            t.rectangle(0, 0, w, h);
            t.fill();

            // Círculo base
            t.set_source_rgba({0.95, 0.95, 0.98, 0.9});
            t.set_line_width(2.0);
            t.arc(center_x, center_y, circle_radius, 0, 2 * M_PI);
            t.stroke();

            return {};
        }
    };
};

MIN_EXTERNAL(tet_circle);
