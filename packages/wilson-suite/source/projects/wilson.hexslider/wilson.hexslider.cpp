#include "c74_min.h"
#include "../../include/wilson_hexslider_kernel.hpp"
#include <vector>
#include <cmath>
#include <unordered_map>

using namespace c74::min;
using namespace c74::min::ui;

/**
 * @brief wilson_hexslider: Superficie de teclado microtonal hexagonal interactiva para Max MSP.
 * Basada en el arquetipo 'kslider' de Max y la geometría de 'Teclados-Wilson' (hexgrid.js).
 * Utiliza el motor gráfico vectorial nativo JGraphics / Min UI.
 */
class wilson_hexslider : public object<wilson_hexslider>, public ui_operator<wilson_hexslider> {
public:
    MIN_DESCRIPTION {"Teclado hexagonal microtonal interactivo basado en Erv Wilson y el arquetipo kslider"};
    MIN_TAGS        {"ui, keyboard, microtonal, wilson, hexgrid, kslider"};
    MIN_AUTHOR      {"OptimizandoParaMaxSDK"};
    MIN_RELATED     {"kslider, nodes, pictslider"};

    // Inlets
    inlet<> input_inlet    { this, "(list / symbol) Control de celdas o asignación de afinación", "anything" };
    inlet<> velocity_inlet { this, "(int) Velocidad por defecto (0-127)", "int" };

    // Outlets (Adoptando la convención de kslider: Pitch a la izquierda, Velocity a la derecha)
    outlet<> pitch_outlet    { this, "(float / ratio) Frecuencia o grado de la celda hexagonal pulsada", "float" };
    outlet<> velocity_outlet { this, "(int) Velocity de la pulsación (0 al soltar, >0 al presionar)", "int" };
    outlet<> metadata_outlet { this, "(list) Metadatos: [index, col, row] de la celda", "list" };

    // Atributos de Inspector
    attribute<int> cols { this, "cols", 39,
        description {"Número de columnas en la retícula hexagonal"},
        range { 3, 100 }
    };

    attribute<int> rows { this, "rows", 25,
        description {"Número de filas en la retícula hexagonal"},
        range { 3, 100 }
    };

    attribute<double> cell_size { this, "cell_size", 12.0,
        description {"Radio de cada hexágono en píxeles"}
    };

    attribute<color> default_color { this, "default_color", color{0.12, 0.12, 0.14, 1.0},
        description {"Color base de celdas inactivas"}
    };

    attribute<color> active_color { this, "active_color", color{0.82, 0.0, 0.0, 1.0},
        description {"Color de celda activa al presionar"}
    };

    // --- Parámetros de Temperamento, Afinación y Octavas (Inspector) ---
    attribute<double> base_freq { this, "base_freq", 261.625565, // C4
        description {"Frecuencia fundamental en Hz para la primera celda / nota base"}
    };

    attribute<int> octave_offset { this, "octave_offset", 0,
        description {"Desplazamiento de octavas (-4 a +4)"},
        range { -4, 4 }
    };

    attribute<symbol> temperament_mode { this, "temperament_mode", "edo",
        description {"Modo de temperamento: 'edo' (divisiones iguales) o 'custom_ratios' (just intonation / wilson)"}
    };

    attribute<double> edo_divisions { this, "edo_divisions", 31.0,
        description {"Número de divisiones iguales de la octava (ej: 12, 19, 31, 41, 53)"},
        range { 1.0, 1200.0 }
    };

    attribute<int> step_x { this, "step_x", 1,
        description {"Pasos de temperamento por cada columna horizontal"}
    };

    attribute<int> step_y { this, "step_y", 5,
        description {"Pasos de temperamento por cada fila vertical (intervalo armónico en 2D)"}
    };

    // Constructor
    wilson_hexslider(const atoms& args = {}) {
        active_cell = -1;
        current_velocity = 100;
    }

    // Manejo de inlet de velocidad (convención kslider)
    message<> int_msg { this, "int", "Recibe número entero para velocidad en inlet 1",
        MIN_FUNCTION {
            if (inlet == 1) {
                current_velocity = std::clamp(static_cast<int>(args[0]), 0, 127);
            }
            return {};
        }
    };

    // Mensaje para cargar ratios personalizados (Just Intonation / Wilson CPS)
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

    // Mensaje de lista plana (recibe directamente la emisión de wilson.core por inlet 0)
    message<> list_msg { this, "list", "Recibe lista de ratios armónicos para activar el seam con generadores de afinación",
        MIN_FUNCTION {
            if (inlet == 0) {
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
    // Rutina de Dibujo Gráfico Vectorial (JGraphics / Canvas)
    // -------------------------------------------------------------
    message<> paint { this, "paint", "Dibuja la retícula hexagonal plana (flat-top)",
        MIN_FUNCTION {
            target ctx { args };
            double r = cell_size.get();
            int c_count = cols.get();
            int r_count = rows.get();
            auto kernel = get_kernel();

            int index = 0;
            for (int row = 0; row < r_count; ++row) {
                for (int col = 0; col < c_count; ++col) {
                    auto center = kernel.get_cell_center(col, row);
                    draw_hexagon(ctx, center.cx, center.cy, r - 1.0, (index == active_cell));
                    index++;
                }
            }
            return {};
        }
    };

    // -------------------------------------------------------------
    // Manejo de Eventos de Ratón (Mouse Interaction)
    // -------------------------------------------------------------
    message<> mousedown { this, "mousedown", "Presiona una celda hexagonal y emite Note-On",
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

    message<> mouseup { this, "mouseup", "Suelta la celda activa y emite Note-Off",
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

    harmos::kernels::wilson::HexsliderKernel get_kernel() const noexcept {
        harmos::kernels::wilson::HexsliderKernel k;
        k.cols = cols.get();
        k.rows = rows.get();
        k.cell_size = cell_size.get();
        k.base_freq = base_freq.get();
        k.octave_offset = octave_offset.get();
        k.temperament_mode = std::string(c74::min::symbol(temperament_mode.get()));
        k.edo_divisions = edo_divisions.get();
        k.step_x = step_x.get();
        k.step_y = step_y.get();
        k.custom_scale_ratios = custom_scale_ratios;
        return k;
    }

    double compute_cell_frequency(int col, int row) const noexcept {
        return get_kernel().compute_cell_frequency(col, row);
    }

    void draw_hexagon(target& ctx, double cx, double cy, double radius, bool is_active) {
        // Flat-top orientation: ángulos en 0, 60, 120, 180, 240, 300 grados
        for (int i = 0; i < 6; ++i) {
            double angle = (c74::min::k_pi / 3.0) * i;
            double px = cx + radius * std::cos(angle);
            double py = cy + radius * std::sin(angle);
            if (i == 0) ctx.move_to({px, py});
            else ctx.line_to({px, py});
        }
        ctx.close_path();

        if (is_active) {
            ctx.fill_preserve(active_color.get());
        } else {
            ctx.fill_preserve(default_color.get());
        }

        ctx.stroke(color{0.05, 0.05, 0.07, 1.0});
    }

    int hit_test(double x, double y) const noexcept {
        return get_kernel().hit_test(x, y);
    }

    void emit_note_on(int cell_index) {
        int c_count = cols.get();
        int col = cell_index % c_count;
        int row = cell_index / c_count;

        // Frecuencia exacta calculada según temperamento, octava y geometría 2D
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
        velocity_outlet.send(0); // Convención kslider: Velocity 0 = Note-Off
        pitch_outlet.send(0.0);
    }
};

MIN_EXTERNAL(wilson_hexslider);
