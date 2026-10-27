"""
Tests TDD para el Extractor de AST de SuperCollider (SCAstExtractor).
Vertical Slice 2: Parseo estático de SynthDef, detección de UGens (.ar / .kr) y síntesis de IR.
"""
import unittest
from core.compiler.sc_ast_extractor import SCAstExtractor, extract_ir_from_sc_source


class TestSCAstExtractor(unittest.TestCase):
    def setUp(self):
        self.extractor = SCAstExtractor()

    def test_extract_synthdef_name_and_arguments(self):
        sc_code = """
        SynthDef(\\simpleOsc, {
            arg out = 0, freq = 440, amp = 0.5, gate = 1;
            var sig = SinOsc.ar(freq) * amp;
            Out.ar(out, sig ! 2);
        }).add;
        """
        ir = self.extractor.extract(sc_code, default_name="simpleOsc")
        self.assertEqual(ir["name"], "simpleOsc")
        self.assertEqual(ir["category"], "dsp")
        
        # Verificar argumentos mapeados a inlets
        inlets = ir["inlets"]
        inlet_names = [inl["description"] for inl in inlets]
        self.assertTrue(any("freq" in d for d in inlet_names))
        self.assertTrue(any("amp" in d for d in inlet_names))
        self.assertTrue(any("gate" in d for d in inlet_names))

    def test_extract_ugens_and_signal_rate(self):
        sc_code = """
        SynthDef(\\fmVoice, {
            arg out = 0, f = 220, c = 1, m1 = 1, i1 = 0, gate = 1;
            var m1Env = EnvGen.kr(Env.adsr(0.01, 0.3, 0.5, 1.0), gate);
            var mod = SinOsc.ar(f * m1) * (f * i1) * m1Env;
            var car = SinOsc.ar(f * c + mod);
            Out.ar(out, car ! 2);
        }).add;
        """
        ir = self.extractor.extract(sc_code, default_name="fmVoice")
        self.assertEqual(ir["name"], "fmVoice")
        self.assertEqual(ir["category"], "dsp")

        # Verificar que se detectaron los UGens en el metadata o algoritmo del IR
        algorithm = ir.get("algorithm", {})
        ugens = algorithm.get("ugens", [])
        ugen_classes = [u["class"] for u in ugens]
        
        self.assertIn("SinOsc", ugen_classes)
        self.assertIn("EnvGen", ugen_classes)
        self.assertIn("Out", ugen_classes)

        # Verificar que el outlet de audio estéreo o mono esté registrado
        outlets = ir["outlets"]
        self.assertGreaterEqual(len(outlets), 1)
        self.assertEqual(outlets[0]["type"], "signal")

    def test_distinguish_ar_vs_kr_rates(self):
        sc_code = """
        SynthDef(\\testRates, {
            arg gate = 1;
            var lfo = LFTri.kr(5);
            var sig = SinOsc.ar(440 + lfo);
            Out.ar(0, sig);
        }).add;
        """
        ir = self.extractor.extract(sc_code)
        ugens = ir["algorithm"]["ugens"]
        
        lfo_ugen = next(u for u in ugens if u["class"] == "LFTri")
        sin_ugen = next(u for u in ugens if u["class"] == "SinOsc")

        self.assertEqual(lfo_ugen["rate"], "control") # .kr
        self.assertEqual(sin_ugen["rate"], "audio")   # .ar


if __name__ == "__main__":
    unittest.main()
