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
import json
import tempfile
import unittest
from pathlib import Path
from core.compiler.contract_engine import ContractEngine, IncompatibleConnectionError, ConnectionAssessment
from scripts.audit import assess_patcher_contracts


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

        # Conexión al outlet de pass-through (`print` está declarado en max_contracts.json)
        res = self.engine.assess_connection("route 1 2 3", 3, "print", 0)
        self.assertEqual(res.status, "VALID")

    def test_bidirectional_signal_control_rejection(self):
        """Señales de audio no deben conectarse a control; control no debe conectarse a señal pura."""
        # 1. Señal de audio hacia inlet de control puro (route inlet 0 es anything) -> INVALID
        res_sig_ctrl = self.engine.assess_connection("cycle~", 0, "route", 0)
        self.assertEqual(res_sig_ctrl.status, "INVALID")
        self.assertIn("audio signal", res_sig_ctrl.reason)

        # 2. Control puro hacia inlet exclusivo de señal (ezdac~ audio in) -> INVALID
        res_ctrl_sig = self.engine.assess_connection("midiformat", 0, "ezdac~", 0)
        self.assertEqual(res_ctrl_sig.status, "INVALID")
        self.assertIn("signal-only inlet", res_ctrl_sig.reason)

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
        # Validación de estructura de IR
        with self.assertRaises(ValueError):
            ContractEngine.from_ir({})
        with self.assertRaises(ValueError):
            ContractEngine.from_ir({"object_name": "missing_ports"})

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

    def test_standard_max_primitives(self):
        """Verifica que las primitivas base añadidas (dac~, adc~, metro, toggle, number, etc.) estén disponibles."""
        # number
        self.assertEqual(len(self.engine.get_inlets("number")), 1)
        self.assertEqual(len(self.engine.get_outlets("number")), 2)

        # dac~ y adc~
        self.assertEqual(len(self.engine.get_inlets("dac~")), 2)
        self.assertEqual(len(self.engine.get_outlets("dac~")), 0)
        self.assertEqual(len(self.engine.get_inlets("adc~")), 0)
        self.assertEqual(len(self.engine.get_outlets("adc~")), 2)

        # metro, toggle, button
        self.assertEqual(len(self.engine.get_inlets("metro")), 2)
        self.assertEqual(len(self.engine.get_outlets("metro")), 1)
        self.assertEqual(len(self.engine.get_inlets("toggle")), 1)
        self.assertEqual(len(self.engine.get_outlets("toggle")), 1)
        self.assertEqual(len(self.engine.get_inlets("button")), 1)
        self.assertEqual(len(self.engine.get_outlets("button")), 1)

        # select, gate, snapshot~
        self.assertEqual(len(self.engine.get_inlets("select")), 2)
        self.assertEqual(len(self.engine.get_outlets("select")), 2)
        self.assertEqual(len(self.engine.get_inlets("gate")), 2)
        self.assertEqual(len(self.engine.get_outlets("gate")), 1)
        self.assertEqual(len(self.engine.get_inlets("snapshot~")), 2)
        self.assertEqual(len(self.engine.get_outlets("snapshot~")), 1)

        # Conexión válida de metro -> button -> toggle
        res1 = self.engine.assess_connection("metro", 0, "button", 0)
        self.assertEqual(res1.status, "VALID")
        res2 = self.engine.assess_connection("button", 0, "toggle", 0)
        self.assertEqual(res2.status, "VALID")

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

    def test_dynamic_arity_poly_and_voice_overlay(self):
        """poly~ debe sintetizar @inlets/@outlets dinamicos y soportar overlay de subpatcher."""
        poly_spec = "poly~ synthVoice 16 @inlets 3 @outlets 4"
        self.assertEqual(len(self.engine.get_inlets(poly_spec)), 3)
        self.assertEqual(len(self.engine.get_outlets(poly_spec)), 4)
        self.assertEqual(self.engine.assess_connection("cycle~", 0, poly_spec, 2).status, "VALID")
        self.assertEqual(self.engine.assess_connection(poly_spec, 3, "gain~", 0).status, "VALID")
        self.assertEqual(self.engine.assess_connection("cycle~", 0, poly_spec, 3).status, "INVALID")
        self.assertEqual(self.engine.assess_connection(poly_spec, 4, "gain~", 0).status, "INVALID")

        voice_overlay = ContractEngine(
            object_contracts={
                "myVoice": {
                    "inlets": [
                        {"id": 0, "name": "gate_in", "type": "int"},
                        {"id": 1, "name": "pitch_sig", "type": "signal"},
                        {"id": 2, "name": "mod_depth", "type": "float"},
                    ],
                    "outlets": [
                        {"id": 0, "name": "out_l", "type": "signal"},
                        {"id": 1, "name": "out_r", "type": "signal"},
                        {"id": 2, "name": "env_done", "type": "bang"},
                    ],
                }
            }
        )
        self.assertEqual(voice_overlay.resolve_inlet_index("poly~ myVoice 8", "mod_depth"), 2)
        self.assertEqual(voice_overlay.resolve_outlet_index("poly~ myVoice 8", "env_done"), 2)

    def test_poly_default_and_dynamic_boundary_cases(self):
        self.assertEqual(self.engine.assess_connection("cycle~", 0, "poly~ fmVoice 16", 0).status, "INVALID")
        self.assertEqual(self.engine.assess_connection("notein", 0, "poly~ fmVoice 16", 1).status, "INVALID")
        self.assertEqual(len(self.engine.get_inlets("poly~ @inlets 3 @outlets 1")), 3)
        self.assertEqual(len(self.engine.get_inlets("poly~ v 8 @inlets 0 @outlets 0")), 1)
        self.assertEqual(len(self.engine.get_outlets("poly~ v 8 @inlets 0 @outlets 0")), 0)
        self.assertEqual(
            self.engine.assess_connection("poly~ v 8 @inlets 0 @outlets 0", 0, "gain~", 0).status,
            "INVALID",
        )
        ov = ContractEngine.from_ir(
            {
                "object_name": "voiceA",
                "inlets": [{"id": 0, "name": "gate", "type": "int"}],
                "outlets": [{"id": 0, "name": "out", "type": "signal"}],
            }
        )
        self.assertEqual(ov.assess_connection("cycle~", 0, "poly~ voiceA 4", 0).status, "INVALID")

    def test_node_script_contract_matches_max9_refpage(self):
        inlets = self.engine.get_inlets("node.script")
        outlets = self.engine.get_outlets("node.script")
        self.assertEqual([p["type"] for p in inlets], ["anything"])
        self.assertEqual([p["type"] for p in outlets], ["anything", "anything"])

        self.assertEqual(self.engine.assess_connection("node.script", 0, "js", 0).status, "VALID")
        self.assertEqual(self.engine.assess_connection("js", 0, "node.script", 0).status, "VALID")
        self.assertEqual(self.engine.assess_connection("cycle~", 0, "node.script", 0).status, "INVALID")
        self.assertEqual(self.engine.assess_connection("message", 0, "node.script", 1).status, "INVALID")
        self.assertEqual(self.engine.assess_connection("node.script", 2, "js", 0).status, "INVALID")

    def test_dict_contract_matches_max9_refpage(self):
        inlets = self.engine.get_inlets("dict")
        outlets = self.engine.get_outlets("dict")
        self.assertEqual([p["type"] for p in inlets], ["anything", "anything"])
        self.assertEqual(
            [p["type"] for p in outlets],
            [
                "anything",
                "anything",
                ["list", "int", "symbol"],
                ["list", "symbol"],
                "anything",
            ],
        )

        self.assertEqual(self.engine.assess_connection("message", 0, "dict", 0).status, "VALID")
        self.assertEqual(self.engine.assess_connection("cycle~", 0, "dict", 0).status, "INVALID")
        self.assertEqual(self.engine.assess_connection("message", 0, "dict", 2).status, "INVALID")
        self.assertEqual(self.engine.assess_connection("dict", 5, "print", 0).status, "INVALID")

    def test_live_bridge_host_patcher_contracts_all_verifiable(self):
        patch_doc = {
            "patcher": {
                "boxes": [
                    {"box": {"id": "obj-node", "maxclass": "newobj", "text": "node.script harmos_live_receiver.js @autostart 1"}},
                    {"box": {"id": "obj-js", "maxclass": "newobj", "text": "js harmos_live_patch.js"}},
                    {"box": {"id": "obj-lb", "maxclass": "newobj", "text": "loadbang"}},
                    {"box": {"id": "obj-msg", "maxclass": "message", "text": "set key1 42"}},
                    {"box": {"id": "obj-dict", "maxclass": "newobj", "text": "dict harmos_test_dict"}},
                ],
                "lines": [
                    {"patchline": {"source": ["obj-node", 0], "destination": ["obj-js", 0]}},
                    {"patchline": {"source": ["obj-js", 0], "destination": ["obj-node", 0]}},
                    {"patchline": {"source": ["obj-lb", 0], "destination": ["obj-msg", 0]}},
                    {"patchline": {"source": ["obj-msg", 0], "destination": ["obj-dict", 0]}},
                ],
            }
        }
        with tempfile.TemporaryDirectory() as tmp:
            patcher_path = Path(tmp) / "host.maxpat"
            patcher_path.write_text(json.dumps(patch_doc), encoding="utf-8")
            result = assess_patcher_contracts(patcher_path, self.engine)
            self.assertEqual(result.violations, [])
            self.assertEqual(result.unverifiable, [])
            self.assertEqual(result.checked, 4)


if __name__ == "__main__":
    unittest.main()
