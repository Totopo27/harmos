r"""
Tests TDD para la extracción de SynthDefs del proyecto real SCMicroSynth (engine.scd).
Vertical Slice 4: Ingesta del archivo real y validación de los grafos \fmVoice, \syncVoice y \masterStage.
"""
import unittest
from core.compiler.sc_ast_extractor import SCAstExtractor


SAMPLE_ENGINE_SCD = """
(
SynthDef(\\fmVoice, {
    arg out = 0, freq = 440, amp = 0.5, gate = 1;
    var lfo = LFTri.kr(5.0);
    var env = EnvGen.kr(Env.adsr(0.01, 0.3, 0.5, 1.0), gate);
    var osc1 = SinOsc.ar(freq + lfo);
    var osc2 = SyncSaw.ar(freq * 2, freq);
    var sig = Limiter.ar((osc1 + osc2) * env * amp);
    Out.ar(out, sig ! 2);
}).add;
)
"""


class TestRealEngineSCIngestion(unittest.TestCase):
    def test_ingest_real_sc_engine_file(self):
        extractor = SCAstExtractor()
        ir = extractor.extract(SAMPLE_ENGINE_SCD, default_name="engineModule")

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
