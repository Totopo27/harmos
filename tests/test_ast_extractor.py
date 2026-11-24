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

    def test_control_flow_keywords_not_extracted_as_messages_or_primary(self):
        ts_code = """
        export class ControlFlowClass {
            process(x: number): number {
                if (x > 0) {
                    while (x > 10) {
                        x -= 1;
                    }
                }
                for (let i = 0; i < 3; i++) {
                    switch (i) {
                        default: break;
                    }
                }
                try {
                    return x;
                } catch (err) {
                    return 0;
                }
            }
        }
        """
        ir = extract_ir_from_ts_source(ts_code, object_name="demo.flow")
        msg_names = {m["name"] for m in ir.get("messages", [])}
        self.assertEqual(msg_names, set())

        ctor_only = """
        export class CtorOnly {
            constructor(seed: number) {
                if (seed > 0) {
                    seed = 1;
                }
            }
        }
        """
        ctor_ir = extract_ir_from_ts_source(ctor_only, object_name="demo.ctor_only")
        self.assertEqual(len(ctor_ir["inlets"]), 1)
        self.assertEqual(ctor_ir["inlets"][0]["type"], "float")
        self.assertEqual(ctor_ir.get("messages", []), [])

    def test_attributes_restricted_to_class_header_not_constructor_or_method_locals(self):
        ts_code = """
        export class ScopedFields {
            gain: number = 1.0;

            constructor() {
                let ctorLocal: number = 42;
            }

            process(x: number): number {
                let methodLocal: number = 7;
                return x * this.gain;
            }
        }
        """
        ir = extract_ir_from_ts_source(ts_code, object_name="demo.scoped")
        attr_names = [a["name"] for a in ir.get("attributes", [])]
        self.assertEqual(attr_names, ["gain"])


if __name__ == "__main__":
    unittest.main()
