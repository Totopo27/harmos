"""
Integration Tests for Harmos CLI Compiler (python -m core.compiler.cli).
Test-Driven Development (TDD) — Testing public behavior at the CLI seam.
"""
import unittest
import json
import tempfile
import os
import shutil
from pathlib import Path

from core.compiler.cli import compile_ir


class TestHarmosCLI(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_compile_control_ir_generates_maxpat_and_cpp(self):
        # IR de prueba válida
        sample_ir = {
            "object_name": "harmos.demo",
            "category": "control",
            "target_runtime": "cpp_min_devkit",
            "inlets": [
                {"id": 0, "type": "float", "description": "Frequency in Hz"},
                {"id": 1, "type": "int", "description": "Trigger velocity"}
            ],
            "outlets": [
                {"id": 0, "type": "float", "description": "Processed output"},
                {"id": 1, "type": "int", "description": "State flag"}
            ],
            "attributes": [
                {"name": "gain", "type": "float", "default": 1.0, "description": "Internal gain factor"}
            ]
        }

        ir_path = os.path.join(self.temp_dir, "demo_ir.json")
        with open(ir_path, "w", encoding="utf-8") as f:
            json.dump(sample_ir, f)

        # Invocar la función pública del compilador
        result = compile_ir(ir_path, output_dir=self.temp_dir)

        # 1. Comprobar que los archivos clave fueron generados
        self.assertTrue(result["success"])
        maxpat_path = result["maxpat_path"]
        cpp_path = result["cpp_path"]
        cmake_path = result["cmake_path"]

        self.assertTrue(os.path.exists(maxpat_path))
        self.assertTrue(os.path.exists(cpp_path))
        self.assertTrue(os.path.exists(cmake_path))

        # 2. Comprobar la validez del patcher de prueba generado
        with open(maxpat_path, "r", encoding="utf-8") as f:
            patch_data = json.load(f)
        self.assertIn("patcher", patch_data)
        boxes = patch_data["patcher"]["boxes"]
        # Debe contener al menos la caja del objeto bajo prueba
        self.assertTrue(any("harmos.demo" in b["box"]["text"] for b in boxes))

        # 3. Comprobar que el C++ generado compila bajo min-devkit
        with open(cpp_path, "r", encoding="utf-8") as f:
            cpp_content = f.read()
        self.assertIn('#include "c74_min.h"', cpp_content)
        self.assertIn("class harmos_demo", cpp_content)
        self.assertIn("inlet<>", cpp_content)
        self.assertIn("outlet<>", cpp_content)

    def test_cli_extract_subcommand_end_to_end(self):
        # Fixture TypeScript
        ts_code = """
        export class GainMeter {
            peak: number = 0.0;
            process(audioIn: number): number {
                return audioIn;
            }
        }
        """
        ts_path = os.path.join(self.temp_dir, "GainMeter.ts")
        with open(ts_path, "w", encoding="utf-8") as f:
            f.write(ts_code)

        ir_out_path = os.path.join(self.temp_dir, "gain_meter.ir.json")

        # Importar la función que gobernará el comando extract
        from core.compiler.cli import handle_extract

        res = handle_extract(ts_path, ir_out_path, object_name="harmos.gain_meter")
        self.assertTrue(res["success"])
        self.assertTrue(os.path.exists(ir_out_path))

        with open(ir_out_path, "r", encoding="utf-8") as f:
            ir_data = json.load(f)

        self.assertEqual(ir_data["object_name"], "harmos.gain_meter")
        self.assertEqual(len(ir_data["inlets"]), 1)
        self.assertEqual(len(ir_data["outlets"]), 1)

        # Encadenamiento directo: compilar la IR recién extraída
        compile_res = compile_ir(ir_out_path, output_dir=self.temp_dir)
        self.assertTrue(compile_res["success"])
        self.assertTrue(os.path.exists(compile_res["maxpat_path"]))
        self.assertTrue(os.path.exists(compile_res["cpp_path"]))



if __name__ == "__main__":
    unittest.main()
