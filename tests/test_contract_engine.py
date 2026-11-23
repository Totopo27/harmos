"""
Tests unitarios exhaustivos para ContractEngine (core/compiler/contract_engine.py).
Cubre:
- Resolución de aridad dinámica (unpack, pack, trigger, t, route).
- Validación bidireccional estricta de tipos (señal vs control).
- Manejo de cajas comment (src y dest inválidas).
- ContractEngine.from_ir() y superposición efímera de contratos.
- Resolución semántica de inlets y outlets.
- Validación con allow_unverifiable.
- Normalización y robustez de tipos de puerto.
"""
import unittest
from core.compiler.contract_engine import ContractEngine, IncompatibleConnectionError, ConnectionAssessment


class TestContractEngine(unittest.TestCase):
    def setUp(self):
        self.engine = ContractEngine()

    def test_dynamic_arity_unpack(self):
        """unpack con argumentos variables debe sintetizar el número y tipo exacto de outlets."""
        # unpack 0 0 0 (3 ints)
        c3 = self.engine.get_object_contract("unpack 0 0 0")
        self.assertIsNotNone(c3)
        outlets = self.engine.get_outlets("unpack 0 0 0")
        self.assertEqual(len(outlets), 3)
        self.assertEqual(outlets[0]["type"], "int")
        self.assertEqual(outlets[1]["type"], "int")
        self.assertEqual(outlets[2]["type"], "int")

        # Conexión a outlet 2 debe ser válida
        res = self.engine.assess_connection("unpack 0 0 0", 2, "mtof", 0)
        self.assertEqual(res.status, "VALID")

        # unpack f f (2 floats)
        outlets_f = self.engine.get_outlets("unpack f f")
        self.assertEqual(len(outlets_f), 2)
        self.assertEqual(outlets_f[0]["type"], "float")
        self.assertEqual(outlets_f[1]["type"], "float")

    def test_dynamic_arity_pack(self):
        """pack con argumentos variables debe sintetizar el número y tipo exacto de inlets."""
        inlets = self.engine.get_inlets("pack 0 0.0 s")
        self.assertEqual(len(inlets), 3)
        self.assertEqual(inlets[0]["type"], "int")
        self.assertEqual(inlets[1]["type"], "float")
        self.assertEqual(inlets[2]["type"], "symbol")

        # Conexión a inlet 2 con symbol
        res = self.engine.assess_connection("unpack 0 0 s", 2, "pack 0 0.0 s", 2)
        self.assertEqual(res.status, "VALID")

    def test_dynamic_arity_trigger(self):
        """trigger y t deben sintetizar outlets ordenados de izquierda a derecha."""
        for t_name in ("trigger b f s", "t b f s"):
            outlets = self.engine.get_outlets(t_name)
            self.assertEqual(len(outlets), 3)
            self.assertEqual(outlets[0]["type"], "bang")
            self.assertEqual(outlets[1]["type"], "float")
            self.assertEqual(outlets[2]["type"], "symbol")

            # Outlets dentro de rango son válidos
            res = self.engine.assess_connection(t_name, 2, "pack s s", 0)
            self.assertEqual(res.status, "VALID")

            # Outlet fuera de rango es INVALID
            res_oob = self.engine.assess_connection(t_name, 3, "pack s s", 0)
            self.assertEqual(res_oob.status, "INVALID")

    def test_dynamic_arity_route(self):
        """route debe sintetizar N outlets de coincidencias + 1 de no-coincidencia."""
        outlets = self.engine.get_outlets("route 1 2 3")
        self.assertEqual(len(outlets), 4) # 3 matches + 1 pass-through
        self.assertEqual(outlets[3]["name"], "unmatched_pass")

        # Conexión al outlet de pass-through
        res = self.engine.assess_connection("route 1 2 3", 3, "print", 0)
        # print no está en catálogo base aún, debe ser UNVERIFIABLE si falta o VALID si tiene contrato
        self.assertIn(res.status, ("VALID", "UNVERIFIABLE"))

    def test_bidirectional_signal_control_rejection(self):
        """Señales de audio no deben conectarse a control; control no debe conectarse a señal pura."""
        # 1. Señal de audio hacia inlet de control puro (route inlet 0 es anything) -> INVALID
        res_sig_ctrl = self.engine.assess_connection("cycle~", 0, "route", 0)
        self.assertEqual(res_sig_ctrl.status, "INVALID")
        self.assertIn("señal de audio", res_sig_ctrl.reason)

        # 2. Control puro hacia inlet exclusivo de señal (ezdac~ audio in) -> INVALID
        res_ctrl_sig = self.engine.assess_connection("midiformat", 0, "ezdac~", 0)
        self.assertEqual(res_ctrl_sig.status, "INVALID")
        self.assertIn("exclusivo de señal", res_ctrl_sig.reason)

        # 3. Control compatible hacia inlet con unión señal/control (cycle~ inlet 0 acepta signal/float) -> VALID
        res_num_cycle = self.engine.assess_connection("mtof", 0, "cycle~", 0)
        self.assertEqual(res_num_cycle.status, "VALID")

        # 4. Señal de audio hacia señal de audio (cycle~ -> gain~) -> VALID
        res_sig_sig = self.engine.assess_connection("cycle~", 0, "gain~", 0)
        self.assertEqual(res_sig_sig.status, "VALID")

    def test_comment_boxes_rejected_bidirectionally(self):
        """Cajas comment carecen de inlets y outlets funcionales."""
        res_dest = self.engine.assess_connection("mtof", 0, "comment", 0)
        self.assertEqual(res_dest.status, "INVALID")

        res_src = self.engine.assess_connection("comment", 0, "mtof", 0)
        self.assertEqual(res_src.status, "INVALID")

    def test_from_ir_overlay(self):
        """from_ir debe superponer temporalmente el contrato del objeto generado."""
        ir = {
            "object_name": "custom.filter~",
            "inlets": [
                {"id": 0, "name": "audio_in", "type": "signal"},
                {"id": 1, "name": "cutoff_hz", "type": "float"}
            ],
            "outlets": [
                {"id": 0, "name": "filtered_audio", "type": "signal"}
            ]
        }
        overlay_engine = ContractEngine.from_ir(ir)
        c = overlay_engine.get_object_contract("custom.filter~")
        self.assertIsNotNone(c)
        self.assertEqual(len(overlay_engine.get_inlets("custom.filter~")), 2)
        self.assertEqual(len(overlay_engine.get_outlets("custom.filter~")), 1)

        # Conectar señal de cycle~ a audio_in de custom.filter~
        res = overlay_engine.assess_connection("cycle~", 0, "custom.filter~", 0)
        self.assertEqual(res.status, "VALID")

        # El motor original no debe estar afectado
        self.assertIsNone(self.engine.get_object_contract("custom.filter~"))

    def test_resolve_outlet_index(self):
        """resolve_outlet_index debe encontrar índices por nombre y alias."""
        idx_sig = self.engine.resolve_outlet_index("adsr~", "envelope_signal")
        self.assertEqual(idx_sig, 0)

        idx_bang = self.engine.resolve_outlet_index("adsr~", "envelope_completed_bang")
        self.assertEqual(idx_bang, 1)

        with self.assertRaises(IncompatibleConnectionError):
            self.engine.resolve_outlet_index("adsr~", "non_existent_role")

    def test_validate_connection_allow_unverifiable(self):
        """validate_connection debe lanzar IncompatibleConnectionError salvo allow_unverifiable=True."""
        # Conexión inválida siempre lanza
        with self.assertRaises(IncompatibleConnectionError):
            self.engine.validate_connection("cycle~", 0, "route", 0)

        # Conexión no verificable (objeto desconocido)
        with self.assertRaises(IncompatibleConnectionError):
            self.engine.validate_connection("unknown.box", 0, "mtof", 0, allow_unverifiable=False)

        # Con allow_unverifiable=True debe retornar el assessment UNVERIFIABLE
        assessment = self.engine.validate_connection("unknown.box", 0, "mtof", 0, allow_unverifiable=True)
        self.assertEqual(assessment.status, "UNVERIFIABLE")

    def test_port_types_robustness(self):
        """port_types debe manejar diccionarios con o sin clave type de forma segura."""
        self.assertEqual(self.engine.port_types({"type": "signal/float"}), {"signal", "float"})
        self.assertEqual(self.engine.port_types({"type": "anything"}), {"anything"})
        self.assertEqual(self.engine.port_types({}), {"anything"})


if __name__ == "__main__":
    unittest.main()
