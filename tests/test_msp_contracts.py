"""
Tests TDD para Contratos MSP de Síntesis y Polifonía (FM, Hard-Sync, Poly~, Envolventes).
Vertical Slice 1: Nuevos contratos en core/schema/max_contracts.json.
"""
import unittest
from core.compiler.contract_engine import ContractEngine, IncompatibleConnectionError


class TestMSPContractEngine(unittest.TestCase):
    def setUp(self):
        self.engine = ContractEngine()

    def test_math_signal_contracts(self):
        # *~ (multiplicador de señales: modulación de amplitud / FM)
        mul_inlets = self.engine.get_inlets("*~")
        self.assertGreaterEqual(len(mul_inlets), 2)
        self.assertEqual(mul_inlets[0]["type"], "signal")
        self.assertEqual(mul_inlets[1]["type"], "signal")
        mul_outlets = self.engine.get_outlets("*~")
        self.assertEqual(len(mul_outlets), 1)
        self.assertEqual(mul_outlets[0]["type"], "signal")

        # +~ (sumador de señales: portadora + offset FM)
        add_inlets = self.engine.get_inlets("+~")
        self.assertGreaterEqual(len(add_inlets), 2)
        self.assertEqual(add_inlets[0]["type"], "signal")
        self.assertEqual(add_inlets[1]["type"], "signal")
        add_outlets = self.engine.get_outlets("+~")
        self.assertEqual(len(add_outlets), 1)
        self.assertEqual(add_outlets[0]["type"], "signal")

    def test_oscillator_contracts(self):
        # phasor~ (rampa / acumulador de fase para sync y lectura de tablas)
        phasor_inlets = self.engine.get_inlets("phasor~")
        self.assertGreaterEqual(len(phasor_inlets), 1)
        self.assertEqual(phasor_inlets[0]["type"], "signal")
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
        self.assertEqual(rect_inlets[0]["type"], "signal")
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


if __name__ == "__main__":
    unittest.main()
