r"""
Tests TDD para la extracción de SynthDefs del proyecto real SCMicroSynth (engine.scd).
Vertical Slice 4: Ingesta del archivo real y validación de los grafos \fmVoice, \syncVoice y \masterStage.
"""
import unittest
from pathlib import Path
from core.compiler.ast_extractor import extract_ir_from_file
from core.compiler.sc_ast_extractor import SCAstExtractor


class TestRealEngineSCIngestion(unittest.TestCase):
    def setUp(self):
        self.engine_path = Path(r"D:\DocumentosDiscoD\SCMicroSynth\modules\engine.scd")

    def test_ingest_real_sc_engine_file(self):
        if not self.engine_path.exists():
            self.skipTest("Ruta local a SCMicroSynth/modules/engine.scd no disponible.")

        with open(self.engine_path, "r", encoding="utf-8") as f:
            code = f.read()

        extractor = SCAstExtractor()
        ir = extractor.extract(code, default_name="engineModule")

        self.assertEqual(ir["category"], "dsp")
        self.assertEqual(ir["algorithm"]["source_language"], "supercollider")
        
        # Verificar que extrajo UGens de audio reales de engine.scd
        ugens = ir["algorithm"]["ugens"]
        ugen_classes = [u["class"] for u in ugens]
        
        self.assertIn("SinOsc", ugen_classes)
        self.assertIn("EnvGen", ugen_classes)
        self.assertIn("LFTri", ugen_classes)
        self.assertIn("SyncSaw", ugen_classes)
        self.assertIn("Limiter", ugen_classes)
        self.assertIn("Out", ugen_classes)

        # Verificar que el outlet de audio estéreo fue inferido
        self.assertEqual(len(ir["outlets"]), 2)
        self.assertEqual(ir["outlets"][0]["type"], "signal")
        self.assertEqual(ir["outlets"][1]["type"], "signal")


if __name__ == "__main__":
    unittest.main()
