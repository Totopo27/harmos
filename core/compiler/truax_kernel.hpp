#pragma once

#include <cmath>
#include <utility>
#include <algorithm>

namespace harmos {
namespace kernels {
namespace truax {

/**
 * @brief Pure C++17 kernel for Barry Truax Normal Form and FM Microtonal Frequency Compensation.
 *
 * Implements the mathematical reduction to Normal Form (C:M ratio) where M >= 2C or 1:1,
 * ensuring the perceived acoustic fundamental matches the intended microtonal pitch.
 */
class TruaxKernel {
public:
    TruaxKernel() = default;

    /**
     * @brief Reduces a carrier-to-modulator (C:M) ratio to Barry Truax Normal Form.
     * @param c Carrier ratio factor
     * @param m Modulator ratio factor
     * @return std::pair<double, double> where first is normal_c and second is normal_m
     */
    static std::pair<double, double> to_normal_form(double c, double m) noexcept {
        double cur_c = std::max(std::abs(c), 0.001);
        double cur_m = std::max(std::abs(m), 0.001);
        int iterations = 0;

        while ((cur_c != cur_m) && (cur_m < (2.0 * cur_c)) && (iterations < 20)) {
            cur_c = std::abs(cur_c - cur_m);
            iterations++;
        }

        return {cur_c, cur_m};
    }

    /**
     * @brief Computes the carrier frequency required so the heard fundamental matches f_fundamental.
     * @param f_fundamental Target acoustic fundamental frequency in Hz
     * @param c Carrier ratio factor
     * @param m Modulator ratio factor
     * @return Required carrier frequency in Hz
     */
    static double calc_carrier_freq(double f_fundamental, double c, double m) noexcept {
        auto [normal_c, normal_m] = to_normal_form(c, m);
        return (f_fundamental * c) / normal_c;
    }
};

} // namespace truax
} // namespace kernels
} // namespace harmos
