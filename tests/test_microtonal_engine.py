"""
Tests TDD para el Módulo de Microtonalidad de Harmos (Truax Normal Form + 384-Tuning Tables).
Valida la compensación matemática de Barry Truax y la generación de coll/buffers para Max MSP.
"""
import unittest
import math
from pathlib import Path
from core.compiler.microtonal_engine import MicrotonalEngine


class TestMicrotonalEngine(unittest.TestCase):
    def setUp(self):
        self.engine = MicrotonalEngine()

    def test_truax_normal_form_identity_and_reduction(self):
        """Verifica la función matemática de Forma Normal de Truax: C = |C - M| hasta M >= 2C o 1:1."""
        # 1:1 ya está en forma normal
        nf_1_1 = self.engine.to_normal_form(1.0, 1.0)
        self.assertAlmostEqual(nf_1_1[0], 1.0)
        self.assertAlmostEqual(nf_1_1[1], 1.0)

        # M >= 2C: 1:2 ya está en forma normal
        nf_1_2 = self.engine.to_normal_form(1.0, 2.0)
        self.assertAlmostEqual(nf_1_2[0], 1.0)
        self.assertAlmostEqual(nf_1_2[1], 2.0)

        # 3:2 -> reducción iterativa: C = |3 - 2| = 1 -> queda 1:2 (M=2, 2*C=2 => M >= 2C)
        nf_3_2 = self.engine.to_normal_form(3.0, 2.0)
        self.assertAlmostEqual(nf_3_2[0], 1.0)
        self.assertAlmostEqual(nf_3_2[1], 2.0)

        # 5:3 -> reducción: C = |5 - 3| = 2 -> queda 2:3 -> C = |2 - 3| = 1 -> queda 1:3
        nf_5_3 = self.engine.to_normal_form(5.0, 3.0)
        self.assertAlmostEqual(nf_5_3[0], 1.0)
        self.assertAlmostEqual(nf_5_3[1], 3.0)

    def test_truax_calc_carrier_freq(self):
        """Calcula fCarrier = (fFundamental * C) / normalC."""
        f_fund = 220.0
        # Caso 1:1 -> normalC = 1 -> fCarrier = 220.0
        f_c1 = self.engine.calc_carrier_freq(f_fund, 1.0, 1.0)
        self.assertAlmostEqual(f_c1, 220.0)

        # Caso 3:2 -> normalC = 1 -> fCarrier = (220.0 * 3) / 1 = 660.0
        f_c2 = self.engine.calc_carrier_freq(f_fund, 3.0, 2.0)
        self.assertAlmostEqual(f_c2, 660.0)

    def test_tuning_tables_length_and_ranges(self):
        """Verifica que cada escala contenga exactamente 384 posiciones (3 canales MIDI)."""
        scales = self.engine.generate_all_scales()
        expected_keys = ["tet12", "tet31", "tet41", "tet53", "meantone31", "magic41", "partch", "centaur"]

        for k in expected_keys:
            self.assertIn(k, scales)
            self.assertEqual(len(scales[k]), 384, f"La escala {k} debe tener exactamente 384 posiciones")
            # Todas las frecuencias deben ser números positivos reales
            self.assertTrue(all(f > 0 for f in scales[k]), f"Todas las frecuencias de {k} deben ser > 0")

    def test_export_max_coll_format(self):
        """Verifica que se pueda exportar en formato de texto 'index, freq;' para el objeto coll de Max."""
        coll_text = self.engine.export_as_coll("tet31")
        lines = coll_text.strip().split("\n")
        self.assertEqual(len(lines), 384)
        self.assertTrue(lines[0].startswith("0,"))
        self.assertTrue(lines[0].endswith(";"))

    def test_generate_truax_js_object(self):
        """Genera el código JavaScript para el objeto [js truax.js] de Max MSP."""
        js_code = self.engine.generate_truax_js()
        self.assertIn("function toNormalForm", js_code)
        self.assertIn("function calcCarrierFreq", js_code)
        self.assertIn("outlet(0", js_code)


if __name__ == "__main__":
    unittest.main()
