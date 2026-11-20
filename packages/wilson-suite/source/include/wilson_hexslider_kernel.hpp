#pragma once
/**
 * @file wilson_hexslider_kernel.hpp
 * @brief Pure C++17 standard kernel for Wilson 2D hexagonal microtonal keyboard.
 * 
 * 100% decoupled from Cycling '74 Max SDK, JGraphics and Min-Devkit.
 * Enables standalone headless evaluation, CI differential testing and mathematical verification.
 */
#include <vector>
#include <cmath>
#include <string>
#include <algorithm>

namespace harmos::kernels::wilson {

struct CellCoord {
    double cx;
    double cy;
};

class HexsliderKernel {
public:
    int cols { 39 };
    int rows { 25 };
    double cell_size { 12.0 };
    double base_freq { 261.625565 }; // C4
    int octave_offset { 0 };
    std::string temperament_mode { "edo" };
    double edo_divisions { 31.0 };
    int step_x { 1 };
    int step_y { 5 };
    std::vector<double> custom_scale_ratios;

    HexsliderKernel() = default;

    // Calcula la frecuencia exacta de una celda hexagonal en coordenadas (col, row)
    double compute_cell_frequency(int col, int row) const noexcept {
        // 1. Fundamental con offset de octava
        double fundamental = base_freq * std::pow(2.0, static_cast<double>(octave_offset));

        // 2. Coordenada relativa en pasos armónicos según los ejes 2D
        int step_count = col * step_x + row * step_y;

        // 3. Modo EDO (Equal Division of Octave)
        if (temperament_mode == "edo") {
            double divisions = edo_divisions;
            if (divisions <= 0.0) divisions = 12.0;
            return fundamental * std::pow(2.0, static_cast<double>(step_count) / divisions);
        }

        // 4. Modo Ratios / Just Intonation / Wilson CPS
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

        // Fallback: 12-EDO
        return fundamental * std::pow(2.0, static_cast<double>(step_count) / 12.0);
    }

    // Calcula la posición euclidiana 2D (cx, cy) del centro de una celda hexagonal
    CellCoord get_cell_center(int col, int row) const noexcept {
        double r = cell_size;
        double sqrt3 = 1.732050807568877;
        double h_spacing = r * 1.5;
        double v_spacing = r * sqrt3;

        double cx = col * h_spacing + r;
        double cy = row * v_spacing + (col % 2 == 1 ? (v_spacing * 0.5) : 0.0) + (r * sqrt3 * 0.5);
        return { cx, cy };
    }

    // Hit-testing euclidiano: dado un punto (x, y) en el canvas, devuelve el índice de la celda impactada o -1
    int hit_test(double x, double y) const noexcept {
        double r = cell_size;
        double r_sq_threshold = r * r * 0.85;

        int index = 0;
        for (int row = 0; row < rows; ++row) {
            for (int col = 0; col < cols; ++col) {
                CellCoord center = get_cell_center(col, row);
                double dx = x - center.cx;
                double dy = y - center.cy;
                if ((dx * dx + dy * dy) <= r_sq_threshold) {
                    return index;
                }
                index++;
            }
        }
        return -1;
    }
};

} // namespace harmos::kernels::wilson
