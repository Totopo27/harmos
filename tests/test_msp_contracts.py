"""
Tests TDD para Contratos MSP de Síntesis y Polifonía (FM, Hard-Sync, Poly~, Envolventes).
Vertical Slice 1: Nuevos contratos en core/schema/max_contracts.json.
"""
import unittest
import json
import os
import tempfile
from pathlib import Path
from core.compiler.contract_engine import ContractEngine, IncompatibleConnectionError


class TestMSPContractEngine(unittest.TestCase):
    def setUp(self):
        self.engine = ContractEngine()

    def test_math_signal_contracts(self):
        # *~ (multiplicador de señales: modulación de amplitud / FM)
        mul_inlets = self.engine.get_inlets("*~")
        self.assertGreaterEqual(len(mul_inlets), 2)
        self.assertEqual(mul_inlets[0]["type"], "signal")
        self.assertEqual(mul_inlets[1]["type"], "signal/float")
        mul_outlets = self.engine.get_outlets("*~")
        self.assertEqual(len(mul_outlets), 1)
        self.assertEqual(mul_outlets[0]["type"], "signal")

        # +~ (sumador de señales: portadora + offset FM)
        add_inlets = self.engine.get_inlets("+~")
        self.assertGreaterEqual(len(add_inlets), 2)
        self.assertEqual(add_inlets[0]["type"], "signal")
        self.assertEqual(add_inlets[1]["type"], "signal/float")
        add_outlets = self.engine.get_outlets("+~")
        self.assertEqual(len(add_outlets), 1)
        self.assertEqual(add_outlets[0]["type"], "signal")

    def test_oscillator_contracts(self):
        # phasor~ (rampa / acumulador de fase para sync y lectura de tablas)
        phasor_inlets = self.engine.get_inlets("phasor~")
        self.assertGreaterEqual(len(phasor_inlets), 1)
        self.assertEqual(phasor_inlets[0]["type"], "signal/float")
        phasor_outlets = self.engine.get_outlets("phasor~")
        self.assertEqual(phasor_outlets[0]["type"], "signal")

        # saw~ (oscilador diente de sierra con banda limitada)
        saw_inlets = self.engine.get_inlets("saw~")
        self.assertGreaterEqual(len(saw_inlets), 1)
        saw_outlets = self.engine.get_outlets("saw~")
        self.assertEqual(saw_outlets[0]["type"], "signal")

        # rect~ (oscilador de pulso / onda cuadrada con control de ancho)
        rect_inlets = self.engine.get_inlets("rect~")
        self.assertGreaterEqual(len(rect_inlets), 2)
        self.assertEqual(rect_inlets[0]["type"], "signal/float")
        rect_outlets = self.engine.get_outlets("rect~")
        self.assertEqual(rect_outlets[0]["type"], "signal")

    def test_envelope_and_dynamics_contracts(self):
        # adsr~ (generador de envolvente ADSR de audio/control)
        adsr_inlets = self.engine.get_inlets("adsr~")
        self.assertGreaterEqual(len(adsr_inlets), 5)
        # 0: gate/trigger, 1: attack, 2: decay, 3: sustain, 4: release
        self.assertEqual(self.engine.resolve_inlet_index("adsr~", "gate"), 0)
        self.assertEqual(self.engine.resolve_inlet_index("adsr~", "attack"), 1)
        self.assertEqual(self.engine.resolve_inlet_index("adsr~", "decay"), 2)
        self.assertEqual(self.engine.resolve_inlet_index("adsr~", "sustain"), 3)
        self.assertEqual(self.engine.resolve_inlet_index("adsr~", "release"), 4)
        adsr_outlets = self.engine.get_outlets("adsr~")
        self.assertGreaterEqual(len(adsr_outlets), 1)
        self.assertEqual(adsr_outlets[0]["type"], "signal")

        # line~ (generador de rampas / envolventes lineales)
        line_inlets = self.engine.get_inlets("line~")
        self.assertGreaterEqual(len(line_inlets), 1)
        line_outlets = self.engine.get_outlets("line~")
        self.assertEqual(line_outlets[0]["type"], "signal")

        # omx.peaklim~ (limitador de picos / brickwall para masterStage)
        lim_inlets = self.engine.get_inlets("omx.peaklim~")
        self.assertGreaterEqual(len(lim_inlets), 2) # audio_left, audio_right
        lim_outlets = self.engine.get_outlets("omx.peaklim~")
        self.assertGreaterEqual(len(lim_outlets), 2)

    def test_polyphony_infrastructure_contracts(self):
        # in~ y out~ (puertos de subpatchers para poly~)
        in_sig_inlets = self.engine.get_inlets("in~")
        self.assertGreaterEqual(len(in_sig_inlets), 1)
        in_sig_outlets = self.engine.get_outlets("in~")
        self.assertEqual(in_sig_outlets[0]["type"], "signal")

        out_sig_inlets = self.engine.get_inlets("out~")
        self.assertGreaterEqual(len(out_sig_inlets), 1)
        self.assertEqual(out_sig_inlets[0]["type"], "signal")

        # thispoly~ (notificador de estado de voz y muteo dinámico)
        thispoly_inlets = self.engine.get_inlets("thispoly~")
        self.assertGreaterEqual(len(thispoly_inlets), 1)
        thispoly_outlets = self.engine.get_outlets("thispoly~")
        self.assertGreaterEqual(len(thispoly_outlets), 1)
        self.assertEqual(thispoly_outlets[0]["type"], "int") # voice index

        # poly~ (contenedor polifónico de subpatchers)
        poly_inlets = self.engine.get_inlets("poly~")
        self.assertGreaterEqual(len(poly_inlets), 1)
        poly_outlets = self.engine.get_outlets("poly~")
        self.assertGreaterEqual(len(poly_outlets), 1)


class TestContractEngineRobustness(unittest.TestCase):
    """Regresion: un objeto sin texto no declara contrato y no debe reventar el motor."""

    def setUp(self):
        self.engine = ContractEngine()

    def test_connection_assessment_distinguishes_missing_evidence(self):
        for args, expected in [
            (("cycle~", 0, "gain~", 0), "VALID"),
            (("cycle~", 0, "mtof", 0), "INVALID"),
            (("unknown.external", 0, "gain~", 0), "UNVERIFIABLE"),
            (("cycle~", -1, "gain~", 0), "INVALID"),
            (("cycle~", 0, "gain~", 9), "INVALID"),
            (("unknown.external", 0, "gain~", 9), "INVALID"),
        ]:
            with self.subTest(args=args):
                result = self.engine.assess_connection(*args)
                self.assertEqual(expected, result.status)
                self.assertTrue(result.reason)
                valid, reason = self.engine.is_valid_connection(*args)
                self.assertEqual(expected == "VALID", valid)
                self.assertTrue(reason)

    def test_empty_object_name_has_no_contract(self):
        self.assertIsNone(self.engine.get_object_contract(""))
        self.assertIsNone(self.engine.get_object_contract("   "))
        self.assertEqual([], self.engine.get_inlets(""))
        self.assertEqual([], self.engine.get_outlets(""))

    def test_connection_with_empty_object_name_is_unverifiable(self):
        valid, reason = self.engine.is_valid_connection("", 0, "mtof", 0)
        self.assertFalse(valid)
        self.assertIn("UNVERIFIABLE", reason)
        valid, reason = self.engine.is_valid_connection("cycle~ 440", 0, "", 0)
        self.assertFalse(valid)
        self.assertIn("UNVERIFIABLE", reason)

    def test_semantic_resolution_never_guesses_a_port(self):
        self.assertEqual(2, self.engine.resolve_inlet_index("midiformat", "cc"))
        self.assertEqual(3, self.engine.resolve_inlet_index("midiformat", "program_change"))
        self.assertEqual(1, self.engine.resolve_inlet_index("lores~", "cutoff"))
        for obj, role in [("", "pitch"), ("midiformat", "velocity"),
                          ("midiformat", "after"), ("cycle~", "")]:
            with self.subTest(obj=obj, role=role):
                with self.assertRaises(IncompatibleConnectionError):
                    self.engine.resolve_inlet_index(obj, role)

    def test_malformed_catalog_is_rejected_instead_of_normalized(self):
        valid = {"objects": {"example": {
            "inlets": {"0": {"name": "input", "type": "signal/float"}},
            "outlets": [],
        }}}
        malformed = [
            {}, {"objects": []},
            {"objects": {"example": {"inlets": [], "outlets": [{"type": "float"}]}}},
            {"objects": {"example": {"inlets": [], "outlets": [{"name": "out", "type": "OUTLET_TYPE"}]}}},
            {"objects": {"example": {"inlets": {"3": {"name": "input", "type": "float"}}, "outlets": []}}},
            {"objects": {"example": {"inlets": [{"id": 2, "name": "input", "type": "float"}], "outlets": []}}},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "contracts.json"
            path.write_text(json.dumps(valid), encoding="utf-8")
            os.utime(path, ns=(1_000_000_000, 1_000_000_000))
            self.assertEqual("signal/float", ContractEngine(str(path)).get_inlets("example")[0]["type"])
            for data in malformed:
                with self.subTest(data=data):
                    path.write_text(json.dumps(data), encoding="utf-8")
                    # Keep the exact same nanosecond timestamp so Windows NTFS tick resolution cannot hide cache bugs.
                    os.utime(path, ns=(1_000_000_000, 1_000_000_000))
                    with self.assertRaises(ValueError):
                        ContractEngine(str(path))
            with self.assertRaises(OSError):
                ContractEngine(str(Path(tmp) / "missing.json"))

    def test_control_float_reaches_signal_float_inlets(self):
        # Max accepts a float on these inlets (it replaces the signal value).
        for obj, inlet in [("*~", 1), ("+~", 1), ("-~", 1), ("phasor~", 0),
                           ("saw~", 0), ("rect~", 0), ("tri~", 0), ("lores~", 1)]:
            with self.subTest(obj=obj, inlet=inlet):
                result = self.engine.assess_connection("flonum", 0, obj, inlet)
                self.assertEqual("VALID", result.status, result.reason)
        # Signal-only inlets still reject control messages.
        self.assertEqual("INVALID", self.engine.assess_connection("flonum", 0, "dac~", 0).status)

    def test_patcher_io_and_active_object_contracts(self):
        expected = {
            "inlet": (0, 1), "outlet": (1, 0), "inlet~": (0, 1), "outlet~": (1, 0),
            "loadbang": (0, 1), "midiout": (2, 0), "sprintf": (1, 1),
            "udpreceive": (1, 2), "udpsend": (2, 0), "jweb": (1, 2),
        }
        for obj, (n_in, n_out) in expected.items():
            with self.subTest(obj=obj):
                self.assertIsNotNone(self.engine.get_object_contract(obj))
                self.assertEqual(n_in, len(self.engine.get_inlets(obj)))
                self.assertEqual(n_out, len(self.engine.get_outlets(obj)))
        self.assertEqual("VALID", self.engine.assess_connection("inlet~", 0, "outlet~", 0).status)
        self.assertEqual("INVALID", self.engine.assess_connection("inlet~", 0, "outlet", 0).status)
        self.assertEqual("VALID", self.engine.assess_connection("loadbang", 0, "metro", 0).status)


if __name__ == "__main__":
    unittest.main()
