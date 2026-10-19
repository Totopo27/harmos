#include "c74_min.h"
#include <vector>
#include <cmath>
#include <algorithm>

using namespace c74::min;
using namespace c74::min::ui;

constexpr double k_pi_val = 3.14159265358979323846;

/**
 * @brief wilson_hexslider: Superficie de teclado microtonal hexagonal interactiva para Max MSP.
 * Basada en el arquetipo 'kslider' de Max y la geometría de 'Teclados-Wilson'.
 * Hereda de ui_operator<320, 180> para soporte vectorial acelerado por hardware (JGraphics).
 */
class wilson_hexslider : public object<wilson_hexslider>, public ui_operator<320, 180> {
public:
    MIN_DESCRIPTION {"Teclado hexagonal microtonal interactivo basado en Erv Wilson y el arquetipo kslider"};
    MIN_TAGS        {"ui, keyboard, microtonal, wilson, hexgrid, kslider"};
    MIN_AUTHOR      {"OptimizandoParaMaxSDK"};
    MIN_RELATED     {"kslider, nodes, pictslider"};

    // Inlets
    inlet<> input_inlet    { this, "(list / symbol) Control de celdas o asignación de afinación", "anything" };
    inlet<> velocity_inlet { this, "(int) Velocidad por defecto (0-127)", "int" };

    // Outlets (Convención kslider: Pitch a la izquierda, Velocity a la derecha)
    outlet<> pitch_outlet    { this, "(float / ratio) Frecuencia o grado de la celda hexagonal pulsada", "float" };
    outlet<> velocity_outlet { this, "(int) Velocity de la pulsación (0 al soltar, >0 al presionar)", "int" };
    outlet<> metadata_outlet { this, "(list) Metadatos: [index, col, row] de la celda", "list" };

    // Atributos de Inspector: Geometría
    attribute<int> cols { this, "cols", 39,
        description {"Número de columnas en la retícula hexagonal"},
        range { 3, 100 },
        setter { MIN_FUNCTION {
            redraw();
            return args;
        }}
    };

    attribute<int> rows { this, "rows", 25,
        description {"Número de filas en la retícula hexagonal"},
        range { 3, 100 },
        setter { MIN_FUNCTION {
            redraw();
            return args;
        }}
    };

    attribute<double> cell_size { this, "cell_size", 12.0,
        description {"Radio de cada hexágono en píxeles (tamaño de tecla para pantallas táctiles/iPad)"},
        range { 6.0, 100.0 },
        setter { MIN_FUNCTION {
            redraw();
            return args;
        }}
    };

    attribute<color> default_color { this, "default_color", color{0.12, 0.12, 0.14, 1.0},
        description {"Color base de celdas inactivas"}
    };

    attribute<color> active_color { this, "active_color", color{0.82, 0.0, 0.0, 1.0},
        description {"Color de celda activa al presionar"}
    };

    // Atributos de Inspector: Afinación y Temperamento
    attribute<double> base_freq { this, "base_freq", 261.625565, // C4 (Hz)
        description {"Frecuencia fundamental en Hz para la primera celda / nota base"}
    };

    attribute<int> octave_offset { this, "octave_offset", 0,
        description {"Desplazamiento de octavas (-4 a +4)"},
        range { -4, 4 }
    };

    attribute<symbol> temperament_mode { this, "temperament_mode", "edo",
        description {"Modo de temperamento: 'edo' o 'custom_ratios'"}
    };

    attribute<double> edo_divisions { this, "edo_divisions", 31.0,
        description {"Número de divisiones iguales de la octava (EDO)"},
        range { 1.0, 1200.0 }
    };

    attribute<int> step_x { this, "step_x", 1,
        description {"Pasos de temperamento por columna horizontal"}
    };

    attribute<int> step_y { this, "step_y", 5,
        description {"Pasos de temperamento por fila vertical (intervalo armónico 2D)"}
    };

    // Constructor obligatorio con ui_operator
    wilson_hexslider(const atoms& args = {})
        : ui_operator::ui_operator {this, args}
    {
        active_cell = -1;
        current_velocity = 100;
    }

    // Mensaje para velocidad entrante en inlet 1 (convención kslider)
    message<> int_msg { this, "int", "Recibe número entero para velocidad en inlet 1",
        MIN_FUNCTION {
            if (inlet == 1) {
                current_velocity = std::clamp(static_cast<int>(args[0]), 0, 127);
            }
            return {};
        }
    };

    // Mensaje para cargar ratios armónicos personalizados (Wilson CPS / Just Intonation)
    message<> set_ratios { this, "set_ratios", "Asigna una lista de ratios armónicos para la escala",
        MIN_FUNCTION {
            custom_scale_ratios.clear();
            for (const auto& item : args) {
                if (item.type() == message_type::float_argument || item.type() == message_type::int_argument) {
                    double r = static_cast<double>(item);
                    if (r > 0.0) custom_scale_ratios.push_back(r);
                }
            }
            if (!custom_scale_ratios.empty()) {
                temperament_mode = c74::min::symbol("custom_ratios");
            }
            return {};
        }
    };

    // Mensaje para limpiar estado visual
    message<> clear { this, "clear", "Apaga todas las celdas iluminadas",
        MIN_FUNCTION {
            if (active_cell != -1) {
                emit_note_off(active_cell);
                active_cell = -1;
                redraw();
            }
            return {};
        }
    };

    // -------------------------------------------------------------
    // Dibujo Vectorial Nativo usando JGraphics (Cairo backend)
    // -------------------------------------------------------------
    message<> paint { this, "paint", "Dibuja la retícula hexagonal vectorial",
        MIN_FUNCTION {
            target t { args };
            c74::max::t_jgraphics* jg = static_cast<c74::max::t_jgraphics*>(t);
            if (!jg) return {};

            double r = cell_size.get();
            int c_count = cols.get();
            int r_count = rows.get();

            double sqrt3 = 1.732050807568877;
            double h_spacing = r * 1.5;
            double v_spacing = r * sqrt3;

            int index = 0;
            for (int row = 0; row < r_count; ++row) {
                for (int col = 0; col < c_count; ++col) {
                    double cx = col * h_spacing + r;
                    double cy = row * v_spacing + (col % 2 == 1 ? (v_spacing * 0.5) : 0.0) + (r * sqrt3 * 0.5);

                    draw_hexagon(jg, cx, cy, r - 1.0, (index == active_cell));
                    index++;
                }
            }
            return {};
        }
    };

    // -------------------------------------------------------------
    // Eventos de Ratón (Comportamiento interactivo kslider)
    // -------------------------------------------------------------
    message<> mousedown { this, "mousedown", "Presiona celda hexagonal y emite Note-On",
        MIN_FUNCTION {
            event e { args };
            int hit = hit_test(e.x(), e.y());
            if (hit != -1) {
                active_cell = hit;
                emit_note_on(active_cell);
                redraw();
            }
            return {};
        }
    };

    message<> mouseup { this, "mouseup", "Suelta celda activa y emite Note-Off",
        MIN_FUNCTION {
            if (active_cell != -1) {
                emit_note_off(active_cell);
                active_cell = -1;
                redraw();
            }
            return {};
        }
    };

    message<> mousedrag { this, "mousedrag", "Desplaza sobre celdas continuas (glissando hexagonal)",
        MIN_FUNCTION {
            event e { args };
            int hit = hit_test(e.x(), e.y());
            if (hit != active_cell) {
                if (active_cell != -1) {
                    emit_note_off(active_cell);
                }
                active_cell = hit;
                if (active_cell != -1) {
                    emit_note_on(active_cell);
                }
                redraw();
            }
            return {};
        }
    };

private:
    int active_cell;
    int current_velocity;
    std::vector<double> custom_scale_ratios;

    void draw_hexagon(c74::max::t_jgraphics* jg, double cx, double cy, double radius, bool is_active) {
        for (int i = 0; i < 6; ++i) {
            double angle = (k_pi_val / 3.0) * i;
            double px = cx + radius * std::cos(angle);
            double py = cy + radius * std::sin(angle);
            if (i == 0) c74::max::jgraphics_move_to(jg, px, py);
            else c74::max::jgraphics_line_to(jg, px, py);
        }
        c74::max::jgraphics_close_path(jg);

        color col = is_active ? active_color.get() : default_color.get();
        c74::max::t_jrgba jcol { col.red(), col.green(), col.blue(), col.alpha() };

        c74::max::jgraphics_set_source_jrgba(jg, &jcol);
        c74::max::jgraphics_fill_preserve(jg);

        // Borde oscuro del hexágono
        c74::max::t_jrgba border_col { 0.05, 0.05, 0.07, 1.0 };
        c74::max::jgraphics_set_source_jrgba(jg, &border_col);
        c74::max::jgraphics_set_line_width(jg, 1.0);
        c74::max::jgraphics_stroke(jg);
    }

    int hit_test(double x, double y) {
        double r = cell_size.get();
        int c_count = cols.get();
        int r_count = rows.get();
        double sqrt3 = 1.732050807568877;
        double h_spacing = r * 1.5;
        double v_spacing = r * sqrt3;

        int index = 0;
        for (int row = 0; row < r_count; ++row) {
            for (int col = 0; col < c_count; ++col) {
                double cx = col * h_spacing + r;
                double cy = row * v_spacing + (col % 2 == 1 ? (v_spacing * 0.5) : 0.0) + (r * sqrt3 * 0.5);

                double dx = x - cx;
                double dy = y - cy;
                if ((dx * dx + dy * dy) <= (r * r * 0.85)) {
                    return index;
                }
                index++;
            }
        }
        return -1;
    }

    double compute_cell_frequency(int col, int row) {
        double fundamental = base_freq.get() * std::pow(2.0, static_cast<double>(octave_offset.get()));
        int step_count = col * step_x.get() + row * step_y.get();

        if (temperament_mode.get() == c74::min::symbol("edo")) {
            double divisions = edo_divisions.get();
            if (divisions <= 0.0) divisions = 12.0;
            return fundamental * std::pow(2.0, static_cast<double>(step_count) / divisions);
        }

        if (!custom_scale_ratios.empty()) {
            int scale_size = static_cast<int>(custom_scale_ratios.size());
            int octave_shift = step_count / scale_size;
            int ratio_idx = step_count % scale_size;
            if (ratio_idx < 0) {
                ratio_idx += scale_size;
                octave_shift -= 1;
            }
            double ratio = custom_scale_ratios[ratio_idx];
            return fundamental * ratio * std::pow(2.0, static_cast<double>(octave_shift));
        }

        return fundamental * std::pow(2.0, static_cast<double>(step_count) / 12.0);
    }

    void emit_note_on(int cell_index) {
        int c_count = cols.get();
        int col = cell_index % c_count;
        int row = cell_index / c_count;

        double pitch_value = compute_cell_frequency(col, row);

        metadata_outlet.send(atoms{ cell_index, col, row });
        velocity_outlet.send(current_velocity);
        pitch_outlet.send(pitch_value);
    }

    void emit_note_off(int cell_index) {
        int c_count = cols.get();
        int col = cell_index % c_count;
        int row = cell_index / c_count;

        metadata_outlet.send(atoms{ cell_index, col, row });
        velocity_outlet.send(0);
        pitch_outlet.send(0.0);
    }
};

MIN_EXTERNAL(wilson_hexslider);
