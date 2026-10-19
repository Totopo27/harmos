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
