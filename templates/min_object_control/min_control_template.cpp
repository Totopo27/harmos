#include "c74_min.h"
#include <vector>
#include <cmath>

using namespace c74::min;

/**
 * @brief Template canónico de objeto de control en Modern C++ (min-devkit)
 * Diseñado para cálculos matemáticos, transformaciones de datos y lógica que corre
 * en el scheduler / main thread de Max MSP.
 */
class min_control_template : public object<min_control_template> {
public:
    MIN_DESCRIPTION {"Objeto de control moderno para Max MSP generado por OptimizandoParaMaxSDK"};
    MIN_TAGS        {"math, control, translation"};
    MIN_AUTHOR      {"OptimizandoParaMaxSDK"};
    MIN_RELATED     {"kslider, coll, dict"};

    // Inlets
    inlet<>  input_inlet   { this, "(list / atoms) Entrada principal de datos o comandos" };
    
    // Outlets
    outlet<> result_outlet { this, "(list / atoms) Salida de datos procesados" };
    outlet<> dump_outlet   { this, "(bang / list) Salida de estado o completitud" };

    // Atributos de Inspector
    attribute<symbol> mode { this, "mode", "default",
        description {"Modo operativo del objeto"}
    };

    // Constructor
    min_control_template(const atoms& args = {}) {
        if (!args.empty()) {
            // Inicializar argumentos pasados en la caja de Max: [mi_objeto arg1 arg2]
        }
    }

    // Manejador de lista / átomos
    message<threadcheck::none> list { this, "list", "Procesa una lista de números o símbolos",
        MIN_FUNCTION {
            atoms output_atoms;
            for (const auto& item : args) {
                if (item.type() == message_type::float_argument) {
                    double val = static_cast<double>(item);
                    output_atoms.push_back(val * 2.0); // Operación de ejemplo
                } else if (item.type() == message_type::int_argument) {
                    int val = static_cast<int>(item);
                    output_atoms.push_back(val * 2);
                }
            }
            result_outlet.send(output_atoms);
            return {};
        }
    };

    // Mensaje Bang
    message<> bang { this, "bang", "Dispara la salida con el último estado calculado",
        MIN_FUNCTION {
            dump_outlet.send(c74::min::symbol("done"));
            return {};
        }
    };
};

MIN_EXTERNAL(min_control_template);
