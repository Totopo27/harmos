"""
Tests TDD para la Síntesis de Parches Polifónicos (poly~) en TypedPatch.
Vertical Slice 3: Creación de subpatchers de voz y contenedores poly~.
"""
import unittest
import json
import tempfile
from core.compiler.typed_patch import TypedPatch, MaxBox


class TestPolyTypedPatch(unittest.TestCase):
    def test_synthesize_voice_subpatcher_with_in_out_thispoly(self):
        patch = TypedPatch()
        
        # Inlets de señal y control
        in_sig = patch.add_box("in~ 1")
        in_gate = patch.add_box("in 2")
        
        # Núcleo de audio FM básico
        osc = patch.add_box("cycle~ 440")
        amp_env = patch.add_box("adsr~ 10 300 0.5 1000")
        mul = patch.add_box("*~")
        
        # Outlets de señal para el poly~
        out_l = patch.add_box("out~ 1")
        out_r = patch.add_box("out~ 2")
        
        # Control de voz dinámico con thispoly~
        thispoly = patch.add_box("thispoly~")

        # Conectar grafo
        patch.connect(osc, 0, mul, 0)
        patch.connect(amp_env, 0, mul, 1)
        patch.connect(mul, 0, out_l, 0)
        patch.connect(mul, 0, out_r, 0)
        patch.connect(in_gate, 0, amp_env, 0) # gate a adsr~
        patch.connect(amp_env, 1, thispoly, 0) # bang de fin de envelope a thispoly~ para liberar/mutear

        with tempfile.NamedTemporaryFile(suffix=".maxpat", delete=False) as f:
            temp_path = f.name

        try:
            patch.save(temp_path)
            with open(temp_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            boxes = data["patcher"]["boxes"]
            box_texts = [b["box"]["text"] for b in boxes]

            self.assertIn("in~ 1", box_texts)
            self.assertIn("out~ 1", box_texts)
            self.assertIn("out~ 2", box_texts)
            self.assertIn("thispoly~", box_texts)
            self.assertIn("adsr~ 10 300 0.5 1000", box_texts)
        finally:
            import os
            if os.path.exists(temp_path):
                os.remove(temp_path)


if __name__ == "__main__":
    unittest.main()
