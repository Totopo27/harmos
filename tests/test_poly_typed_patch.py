"""
Tests TDD para la Síntesis de Parches Polifónicos (poly~) en TypedPatch.
Vertical Slice 3: Creación de subpatchers de voz y contenedores poly~.
"""
import unittest
import json
import tempfile
from pathlib import Path
from core.compiler.typed_patch import TypedPatch, MaxBox
from scripts.audit import audit_contracts


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

        # Conectar grafo mediante resolución semántica (Zero Hardcoding)
        patch.connect_semantic(osc, "audio_out", mul, "audio_in_a")
        patch.connect_semantic(amp_env, "envelope_signal", mul, "audio_in_b_or_gain")
        patch.connect_semantic(mul, "multiplied_audio", out_l, "signal_input")
        patch.connect_semantic(mul, "multiplied_audio", out_r, "signal_input")
        patch.connect_semantic(in_gate, 0, amp_env, "gate_trigger")
        patch.connect_semantic(amp_env, "envelope_completed_bang", thispoly, "mute_or_voice_messages")

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

            # Verificación formal de contratos en el patcher sintetizado
            violations, total_cords = audit_contracts(Path(temp_path))
            self.assertEqual(len(violations), 0, f"Contract violations in voice subpatcher: {violations}")
            self.assertEqual(total_cords, 6)
        finally:
            import os
            if os.path.exists(temp_path):
                os.remove(temp_path)


if __name__ == "__main__":
    unittest.main()
