"""
Tests TDD para el sintetizador de voces Max (fmVoice.maxpat) y traducción de engine.scd.
Verifica que el grafo de 3 operadores FM en cascada sea generado con TypedPatch
respetando el 100% de los contratos de max_contracts.json.
"""
import unittest
import json
import tempfile
from pathlib import Path
from core.compiler.cli import compile_ir
from core.compiler.contract_engine import ContractEngine
from core.compiler.sc_ast_extractor import SCAstExtractor
from core.compiler.sc_voice_compiler import SCVoiceCompiler
from scripts.audit import assess_patcher_contracts, audit_contracts, audit_provenance


class TestFMVoiceCompiler(unittest.TestCase):
    def setUp(self):
        self.compiler = SCVoiceCompiler()

    def test_synthesize_fm_voice_patcher(self):
        """Verifica la generación del subpatcher fmVoice.maxpat con 3 operadores y poly~ control."""
        with tempfile.NamedTemporaryFile(suffix=".maxpat", delete=False) as f:
            temp_path = f.name

        try:
            res = self.compiler.compile_fm_voice(temp_path)
            self.assertTrue(res["success"])
            self.assertTrue(Path(temp_path).exists())

            with open(temp_path, "r", encoding="utf-8") as f:
                patch_data = json.load(f)

            boxes = patch_data["patcher"]["boxes"]
            box_texts = [b["box"]["text"] for b in boxes]
            lines = patch_data["patcher"]["lines"]

            # 1. Inlets y Outlets de poly~
            self.assertTrue(any(t.startswith("in~ 1") for t in box_texts), "Debe tener in~ 1 para frecuencia o señal")
            self.assertTrue(any(t.startswith("in 2") or t.startswith("in~ 2") for t in box_texts), "Debe tener inlet para gate/trigger")
            self.assertTrue(any(t.startswith("out~ 1") for t in box_texts), "Debe tener out~ 1")
            self.assertTrue(any(t.startswith("out~ 2") for t in box_texts), "Debe tener out~ 2")
            self.assertTrue(any("thispoly~" in t for t in box_texts), "Debe incluir thispoly~ para voice control")

            # 2. Operadores de síntesis (3 osciladores de fase / cycle~)
            cycle_boxes = [t for t in box_texts if t.startswith("cycle~")]
            self.assertGreaterEqual(len(cycle_boxes), 3, "Debe contener al menos 3 cycle~ (Carrier, Mod1, Mod2)")

            # 3. Sumas y Multiplicaciones de modulación (+~ y *~)
            self.assertTrue(any(t.startswith("+~") for t in box_texts), "Debe contener sumadores de señal para modulación de fase/frecuencia")
            self.assertTrue(any(t.startswith("*~") for t in box_texts), "Debe contener multiplicadores de señal para índice/envolvente")

            # 4. Envolventes de modulación y carrier (adsr~)
            adsr_boxes = [t for t in box_texts if t.startswith("adsr~")]
            self.assertGreaterEqual(len(adsr_boxes), 1, "Debe contener generadores de envolvente adsr~")

            # 5. Integridad de cables (patchlines)
            self.assertGreater(len(lines), 5, "El parche debe tener conexiones válidas entre operadores")

            # 6. Verificación de caja message "0" entre adsr~ y thispoly~
            box_by_id = {b["box"]["id"]: b["box"] for b in boxes}
            msg_boxes = [b for b in box_by_id.values() if b.get("maxclass") == "message" and b.get("text") == "0"]
            self.assertEqual(len(msg_boxes), 1, "Debe incluir caja message '0' para liberar la voz")
            msg_id = msg_boxes[0]["id"]
            cords = [(ln["patchline"]["source"], ln["patchline"]["destination"]) for ln in lines]
            self.assertTrue(
                any(box_by_id[s[0]]["text"].startswith("adsr~") and s[1] == 1 and d == [msg_id, 0] for s, d in cords)
            )
            self.assertTrue(
                any(s == [msg_id, 0] and box_by_id[d[0]]["text"] == "thispoly~" and d[1] == 0 for s, d in cords)
            )

            # 7. Verificación formal de contratos en el patcher sintetizado
            audit_res = assess_patcher_contracts(Path(temp_path))
            self.assertEqual(audit_res.violations, [], f"Contract violations in fmVoice: {audit_res.violations}")
            self.assertEqual(audit_res.unverifiable, [], f"Unverifiable cords in fmVoice: {audit_res.unverifiable}")
            self.assertGreater(audit_res.checked, 0)

        finally:
            import os
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_sc_voice_compiler_uses_semantic_connections_only(self):
        source = Path("core/compiler/sc_voice_compiler.py").read_text(encoding="utf-8")
        self.assertNotIn("patch.connect(", source)
        self.assertIn("patch.connect_semantic(", source)

    def test_sc_to_ir_cpp_patcher_audit_end_to_end(self):
        """End-to-end: SC SynthDef + control -> IR -> C++/Patcher/Maxref -> Contract & Provenance audit."""
        sc_source = r"""
        (
        scales[\custom24] = self.build24;
        SynthDef(\harmosVoice, {
            arg out = 0, freq = 440, gate = 1;
            var env = EnvGen.kr(Env.adsr(0.01, 0.2, 0.5, 0.4), gate);
            var sig = SinOsc.ar(freq) * env;
            Out.ar(out, sig ! 2);
        }).add;
        )
        """
        ir = SCAstExtractor().extract(sc_source, default_name="harmosVoice")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ir_path = root / "harmosVoice.ir.json"
            ir_path.write_text(json.dumps(ir), encoding="utf-8")

            pkg_dir = root / "pkg"
            compiled = compile_ir(str(ir_path), str(pkg_dir), build=False)
            self.assertTrue(compiled["success"])
            maxpat_path = Path(compiled["maxpat_path"])
            self.assertTrue(Path(compiled["cpp_path"]).is_file())
            self.assertTrue(Path(compiled["kernel_path"]).is_file())
            self.assertTrue(Path(compiled["maxref_path"]).is_file())

            prov_verdict, prov_details = audit_provenance(maxpat_path, ir_path=ir_path)
            self.assertEqual(prov_verdict, "VALID", prov_details)

            pkg_audit = assess_patcher_contracts(maxpat_path, ContractEngine.from_ir(ir))
            self.assertEqual(pkg_audit.violations, [])
            self.assertEqual(pkg_audit.unverifiable, [])

            voice_path = pkg_dir / "harmosVoice_voice.maxpat"
            main_path = pkg_dir / "harmosVoice_main.maxpat"
            self.compiler.compile_fm_voice(str(voice_path), ir_data=ir)
            self.compiler.compile_main_synth(str(main_path), voice_patcher_name="harmosVoice_voice", control_ir=ir)

            for p in (voice_path, main_path):
                res = assess_patcher_contracts(p)
                self.assertEqual(res.violations, [], res)
                self.assertEqual(res.unverifiable, [], res)
            main_texts = [b["box"]["text"] for b in json.loads(main_path.read_text(encoding="utf-8"))["patcher"]["boxes"]]
            self.assertIn("coll custom24.txt", main_texts)


if __name__ == "__main__":
    unittest.main()
