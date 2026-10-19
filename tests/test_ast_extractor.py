"""
Unit Tests for Harmos TypeScript AST Extractor (core.compiler.ast_extractor).
Test-Driven Development (TDD) — Testing public behavior at the extraction seam.
"""
import unittest
import json
import tempfile
import os
import shutil

from core.compiler.ast_extractor import extract_ir_from_ts_source, extract_ir_from_file


class TestAstExtractor(unittest.TestCase):
    def test_extract_simple_dsp_processor_ts(self):
        ts_code = """
        export class LfoFilter {
            gain: number = 1.0;

            constructor(rate: number, depth: number) {}

            process(audioIn: number, cutoff: number): number {
                return audioIn * this.gain;
            }

            reset(): void {
                this.gain = 1.0;
            }
        }
        """

        ir = extract_ir_from_ts_source(ts_code, object_name="demo.lfo_filter")

        self.assertEqual(ir["object_name"], "demo.lfo_filter")
        self.assertEqual(ir["target_runtime"], "cpp_min_devkit")
        self.assertIn(ir["category"], ["control", "dsp"])

        # Inlets: mapeados a partir de los parámetros de process (audioIn, cutoff)
        inlets = ir["inlets"]
        self.assertEqual(len(inlets), 2)
        self.assertEqual(inlets[0]["type"], "float")
        self.assertEqual(inlets[1]["type"], "float")

        # Outlets: valor de retorno de process (: number)
        outlets = ir["outlets"]
        self.assertEqual(len(outlets), 1)
        self.assertEqual(outlets[0]["type"], "float")

        # Mensajes adicionales: reset()
        messages = ir.get("messages", [])
        self.assertTrue(any(m["name"] == "reset" for m in messages))

    def test_extract_array_return_maps_to_list_outlet(self):
        ts_code = """
        export function calculateHarmonics(fundamental: number, count: number): number[] {
            let res: number[] = [];
            for (let i = 1; i <= count; i++) {
                res.push(fundamental * i);
            }
            return res;
        }
        """

        ir = extract_ir_from_ts_source(ts_code, object_name="harmos.harmonics")

        self.assertEqual(ir["object_name"], "harmos.harmonics")
        inlets = ir["inlets"]
        self.assertEqual(len(inlets), 2)
        self.assertEqual(inlets[0]["type"], "float")
        self.assertEqual(inlets[1]["type"], "int")

        outlets = ir["outlets"]
        self.assertEqual(len(outlets), 1)
        # Retorno number[] se mapea a 'list'
        self.assertEqual(outlets[0]["type"], "list")


if __name__ == "__main__":
    unittest.main()
