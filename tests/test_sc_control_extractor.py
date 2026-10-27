"""
Tests TDD para el Extractor de Control y Tablas de SuperCollider (SCControlExtractor).
Verifica la extracción estática de diccionarios de afinación (tunings.scd), generadores de arrays,
y la síntesis automática de la sección data_tables y control_interfaces en la IR.
"""
import unittest
from pathlib import Path
from core.compiler.sc_control_extractor import SCControlExtractor


class TestSCControlExtractor(unittest.TestCase):
    def setUp(self):
        self.extractor = SCControlExtractor()
        self.tunings_path = Path(r"D:\DocumentosDiscoD\SCMicroSynth\modules\tunings.scd")

    def test_extract_scales_and_methods_from_tunings_code(self):
        """Verifica la detección automática de todas las escalas definidas en tunings.scd."""
        if not self.tunings_path.exists():
            self.skipTest("Ruta local a SCMicroSynth/modules/tunings.scd no disponible.")

        with open(self.tunings_path, "r", encoding="utf-8") as f:
            code = f.read()

        control_ir = self.extractor.extract(code, module_name="tuningsModule")

        # 1. Metadatos básicos
        self.assertEqual(control_ir["category"], "control")

        # 2. Tablas de datos detectadas
        data_tables = control_ir.get("data_tables", [])
        table_names = [t["name"] for t in data_tables]

        self.assertIn("tet31", table_names)
        self.assertIn("tet41", table_names)
        self.assertIn("tet53", table_names)
        self.assertIn("tet12", table_names)
        self.assertIn("meantone31", table_names)
        self.assertIn("magic41", table_names)
        self.assertIn("partch", table_names)
        self.assertIn("centaur", table_names)

        # 3. Interfaz de control automática generada
        control_interfaces = control_ir.get("control_interfaces", [])
        self.assertGreaterEqual(len(control_interfaces), 1)

        scale_selector = control_interfaces[0]
        self.assertEqual(scale_selector["ui_type"], "umenu")
        self.assertEqual(scale_selector["target_table"], "tuning_coll")
        self.assertIn("tet31.txt", scale_selector["options"])
        self.assertIn("partch.txt", scale_selector["options"])


if __name__ == "__main__":
    unittest.main()
