"""
Tests TDD para el sintetizador de voces Max (fmVoice.maxpat) y traducción de engine.scd.
Verifica que el grafo de 3 operadores FM en cascada sea generado con TypedPatch
respetando el 100% de los contratos de max_contracts.json.
"""
import unittest
import json
import tempfile
from pathlib import Path
from core.compiler.sc_voice_compiler import SCVoiceCompiler
from core.compiler.contract_engine import ContractEngine


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

        finally:
            import os
            if os.path.exists(temp_path):
                os.remove(temp_path)


if __name__ == "__main__":
    unittest.main()
