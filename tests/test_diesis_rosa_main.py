"""
Tests TDD para el Compilador del Sintetizador diesisRosa en Max MSP (diesisRosa.maxpat).
Ensambla el patcher principal con:
- Entrada MIDI (notein)
- Mapeo Microtonal (coll con 384 afinaciones)
- Compensación de Fundamental por Forma Normal de Barry Truax ([js truax.js])
- Motor de síntesis polifónica ([poly~ fmVoice 16])
- Etapa de salida estéreo con limitador de protección y control de volumen (omx.peaklim~ / gain~ / ezdac~)
"""
import unittest
import json
import tempfile
from pathlib import Path
from core.compiler.sc_voice_compiler import SCVoiceCompiler


class TestDiesisRosaMainPatcher(unittest.TestCase):
    def setUp(self):
        self.compiler = SCVoiceCompiler()

    def test_compile_diesis_rosa_main_patcher(self):
        with tempfile.NamedTemporaryFile(suffix=".maxpat", delete=False) as f:
            temp_path = f.name

        try:
            res = self.compiler.compile_main_synth(temp_path, voice_patcher_name="fmVoice", polyphony=16)
            self.assertTrue(res["success"])
            self.assertTrue(Path(temp_path).exists())

            with open(temp_path, "r", encoding="utf-8") as patch_f:
                patch_data = json.load(patch_f)

            boxes = patch_data["patcher"]["boxes"]
            box_texts = [b["box"]["text"] for b in boxes]
            lines = patch_data["patcher"]["lines"]

            # 1. Contenedor polifónico poly~
            self.assertTrue(any("poly~ fmVoice 16" in t for t in box_texts), "Debe instanciar [poly~ fmVoice 16]")

            # 2. Entrada MIDI
            self.assertTrue(any("notein" in t for t in box_texts), "Debe contener entrada [notein]")

            # 3. Mapeador de afinación microtonal (coll)
            self.assertTrue(any("coll" in t for t in box_texts), "Debe contener tabla [coll]")

            # 4. Compensación de Forma Normal de Truax (js)
            self.assertTrue(any("js truax.js" in t for t in box_texts), "Debe contener el calculador [js truax.js]")

            # 5. Salida de audio protegida (ezdac~)
            self.assertTrue(any("ezdac~" in t for t in box_texts), "Debe contener salida [ezdac~]")

            # 6. Conexiones
            self.assertGreater(len(lines), 6, "El parche principal debe tener conexiones completas")

        finally:
            import os
            if os.path.exists(temp_path):
                os.remove(temp_path)


if __name__ == "__main__":
    unittest.main()
