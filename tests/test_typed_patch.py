"""
Tests for Harmos Contract Engine & TypedPatch Compiler.
Test-Driven Development (TDD) — Testing public behavior at the seam.
"""
import unittest
import json
import tempfile
import os
from pathlib import Path

# The module under test (will be implemented next)
from core.compiler.typed_patch import TypedPatch
from core.compiler.contract_engine import ContractEngine, IncompatibleConnectionError


class TestContractEngine(unittest.TestCase):
    def setUp(self):
        self.engine = ContractEngine()

    def test_lookup_known_object_inlets(self):
        inlets = self.engine.get_inlets("midiformat")
        self.assertEqual(len(inlets), 7)
        self.assertEqual(inlets[0]["type"], "int")
        self.assertEqual(inlets[5]["type"], "int")
        self.assertEqual(inlets[6]["type"], "int")

    def test_resolve_inlet_by_semantic_role(self):
        inlet_idx = self.engine.resolve_inlet_index("midiformat", "pitch_bend")
        self.assertEqual(inlet_idx, 5)

        channel_idx = self.engine.resolve_inlet_index("midiformat", "channel")
        self.assertEqual(channel_idx, 6)

    def test_prohibit_connection_to_comment(self):
        with self.assertRaises(IncompatibleConnectionError):
            self.engine.validate_connection("cycle~", 0, "comment", 0)

    def test_signal_auto_summing_rule(self):
        can_connect, reason = self.engine.is_valid_connection("cycle~", 0, "gain~", 0)
        self.assertTrue(can_connect)
        self.assertIn("signal", reason)

    def test_expanded_control_contracts(self):
        # scale: 0: input, 1: in_low, 2: in_high, 3: out_low, 4: out_high
        scale_inlets = self.engine.get_inlets("scale")
        self.assertEqual(len(scale_inlets), 5)
        self.assertEqual(self.engine.resolve_inlet_index("scale", "in_low"), 1)
        self.assertEqual(self.engine.resolve_inlet_index("scale", "out_high"), 4)

        # mtof: 0: midi_pitch -> outlet: freq_hz
        mtof_inlets = self.engine.get_inlets("mtof")
        self.assertEqual(len(mtof_inlets), 1)
        mtof_outlets = self.engine.get_outlets("mtof")
        self.assertEqual(mtof_outlets[0]["type"], "float")

        # unpack: inlets y outlets de tipos
        unpack_inlets = self.engine.get_inlets("unpack")
        self.assertEqual(unpack_inlets[0]["type"], "list")

    def test_expanded_dsp_contracts(self):
        # lores~: 0: audio_in, 1: cutoff_freq, 2: resonance
        lores_inlets = self.engine.get_inlets("lores~")
        self.assertEqual(len(lores_inlets), 3)
        self.assertEqual(self.engine.resolve_inlet_index("lores~", "cutoff"), 1)
        self.assertEqual(self.engine.resolve_inlet_index("lores~", "resonance"), 2)

        # clip~: 0: audio_in, 1: min, 2: max
        clip_inlets = self.engine.get_inlets("clip~")
        self.assertEqual(len(clip_inlets), 3)
        self.assertEqual(self.engine.resolve_inlet_index("clip~", "min"), 1)

        # plugin~ and plugout~
        plugin_outlets = self.engine.get_outlets("plugin~")
        self.assertEqual(len(plugin_outlets), 2)
        plugout_inlets = self.engine.get_inlets("plugout~")
        self.assertEqual(len(plugout_inlets), 2)



class TestTypedPatch(unittest.TestCase):
    def test_create_valid_maxpat_structure(self):
        patch = TypedPatch()
        osc = patch.add_box("cycle~ 440")
        gain = patch.add_box("gain~")
        dac = patch.add_box("ezdac~")

        patch.connect(osc, 0, gain, 0)
        patch.connect(gain, 0, dac, 0)
        patch.connect(gain, 0, dac, 1)

        with tempfile.NamedTemporaryFile(suffix=".maxpat", delete=False) as f:
            temp_path = f.name

        try:
            patch.save(temp_path)
            with open(temp_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.assertIn("patcher", data)
            self.assertIn("boxes", data["patcher"])
            self.assertIn("lines", data["patcher"])
            self.assertEqual(len(data["patcher"]["boxes"]), 3)
            self.assertEqual(len(data["patcher"]["lines"]), 3)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_semantic_role_connection(self):
        patch = TypedPatch()
        midi_ctrl = patch.add_box("notein")
        midi_fmt = patch.add_box("midiformat")

        # Connect pitch to note_inlet (0)
        patch.connect_semantic(midi_ctrl, 0, midi_fmt, "pitch")
        # Connect channel to channel_inlet (6)
        patch.connect_semantic(midi_ctrl, 2, midi_fmt, "channel")

        data = patch.to_dict()
        lines = data["patcher"]["lines"]
        self.assertEqual(lines[0]["patchline"]["destination"][1], 0)
        self.assertEqual(lines[1]["patchline"]["destination"][1], 6)

    def test_block_invalid_connection(self):
        patch = TypedPatch()
        osc = patch.add_box("cycle~ 440")
        note = patch.add_box("comment Anotacion")

        with self.assertRaises(IncompatibleConnectionError):
            patch.connect(osc, 0, note, 0)


if __name__ == "__main__":
    unittest.main()
