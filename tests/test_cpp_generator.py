"""
Tests unitarios para la generación C++ desacoplada (core/compiler/cpp_generator.py).
Verifica que el kernel C++ sea puro (sin cabeceras de Cycling '74 Max) y que el wrapper
Min-Devkit delegue la lógica correctamente.
"""
import unittest
import tempfile
import os
import json
from pathlib import Path

from core.compiler.cpp_generator import generate_cpp_kernel, generate_min_wrapper
from core.compiler.cli import compile_ir


class TestCppGenerator(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)

        self.sample_ir = {
            "object_name": "harmos.gain_limiter",
            "category": "dsp",
            "target_runtime": "cpp_min_devkit",
            "inlets": [
                {"id": 0, "type": "signal", "description": "Audio input"}
            ],
            "outlets": [
                {"id": 0, "type": "signal", "description": "Audio output"}
            ],
            "attributes": [
                {"name": "ceiling", "type": "float", "default": 0.95, "description": "Ceiling level"},
                {"name": "oversample_mode", "type": "int", "default": 2, "description": "Oversampling"}
            ]
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_kernel_has_zero_max_sdk_dependencies(self):
        """El kernel debe ser 100% C++ estándar puro para permitir compilación headless en CI."""
        kernel_src = generate_cpp_kernel(self.sample_ir)

        # Reglas duras de desacoplamiento
        self.assertNotIn("c74_min.h", kernel_src)
        self.assertNotIn("c74::min", kernel_src)
        self.assertNotIn("object<", kernel_src)
        self.assertNotIn("inlet<", kernel_src)
        self.assertNotIn("outlet<", kernel_src)
        self.assertNotIn("MIN_EXTERNAL", kernel_src)

        # Debe contener la estructura pura
        self.assertIn("#pragma once", kernel_src)
        self.assertIn("class harmos_gain_limiterKernel", kernel_src)
        self.assertIn("double ceiling{0.95};", kernel_src)
        self.assertIn("int oversample_mode{2};", kernel_src)
        self.assertIn("process_sample", kernel_src)
        self.assertIn("process_block", kernel_src)

    def test_min_wrapper_delegates_to_kernel(self):
        """El wrapper de Min-Devkit debe alojar el kernel y conectar inlets/outlets."""
        wrapper_src = generate_min_wrapper(self.sample_ir, "gain_limiter_kernel.hpp")

        self.assertIn('#include "c74_min.h"', wrapper_src)
        self.assertIn('#include "gain_limiter_kernel.hpp"', wrapper_src)
        self.assertIn("class harmos_gain_limiter : public object<harmos_gain_limiter>", wrapper_src)
        self.assertIn("harmos::kernels::harmos_gain_limiterKernel m_kernel;", wrapper_src)
        self.assertIn("MIN_EXTERNAL(harmos_gain_limiter);", wrapper_src)

    def test_compile_ir_emits_both_kernel_and_wrapper(self):
        """compile_ir debe emitir tanto el kernel puro como el wrapper y registrarlos en la procedencia."""
        ir_file = self.dir_path / "limiter.ir.json"
        with open(ir_file, "w", encoding="utf-8") as f:
            json.dump(self.sample_ir, f)

        res = compile_ir(str(ir_file), str(self.dir_path))
        self.assertTrue(res["success"])

        # Verificar existencia de artefactos desacoplados
        kernel_path = Path(res["kernel_path"])
        cpp_path = Path(res["cpp_path"])

        self.assertTrue(kernel_path.is_file())
        self.assertTrue(cpp_path.is_file())
        self.assertTrue(kernel_path.name.endswith("_kernel.hpp"))
        self.assertTrue(cpp_path.name.endswith(".cpp"))

        # El wrapper debe referenciar al header del kernel
        wrapper_content = cpp_path.read_text(encoding="utf-8")
        self.assertIn(kernel_path.name, wrapper_content)

    def test_wilson_kernel_pure_header_integrity(self):
        """Verifica que el pilot case wilson_kernel.hpp no tenga dependencias de Min-Devkit."""
        repo_root = Path(__file__).resolve().parent.parent
        wilson_kernel_path = repo_root / "benchmarks" / "teclados-wilson" / "wilson_kernel.hpp"
        self.assertTrue(wilson_kernel_path.is_file())

        content = wilson_kernel_path.read_text(encoding="utf-8")
        self.assertNotIn("c74_min.h", content)
        self.assertNotIn("c74::min", content)
        self.assertIn("class WilsonKernel", content)
        self.assertIn("reduce_to_octave", content)
        self.assertIn("get_combinations", content)


if __name__ == "__main__":
    unittest.main()
