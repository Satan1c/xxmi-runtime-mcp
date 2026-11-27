import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from input_keys import press, translate
from runtime import bindings, completed_dump, frozen_fps, hashes, marked_hash, performance, selection


class RuntimeTests(unittest.TestCase):
    def test_latest_registrations(self):
        log = "[Hunting]\n  analyse_frame=F8\n  toggle_hunting=F3\n[System]\n"
        log += "[Hunting]\n  analyse_frame=ctrl no_shift F6\n[KeyOther]\n  analyse_frame=F4"
        self.assertEqual(bindings(log), {"analyse_frame": "ctrl no_shift F6"})

    def test_stock_hunting_binding(self):
        self.assertEqual(translate("no_modifiers NO_VK_DECIMAL VK_NUMPAD2"), [("KP_2", 98)])
        self.assertEqual(translate("VK_DECIMAL VK_NUMPAD2"), [("KP_Decimal", 110), ("KP_2", 98)])

    def test_wrong_window_does_not_send(self):
        with patch("input_keys.focused_window", return_value=10):
            with self.assertRaisesRegex(RuntimeError, "must have focus"):
                press("F8", 20, 100)

    def test_dump_requires_completion_and_new_dir(self):
        name = "FrameAnalysis-2026-11-27-123456"
        log = f"Frame analysis saved to Z:\\game\\{name}\n"
        self.assertIsNone(completed_dump(log, {}))
        self.assertEqual(completed_dump(log, {name: Path(name)}), name)

    def test_exact_hash_search(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "log.txt").write_text("a00112233b\nhash=00112233\n")
            (root / "ib=00112233.txt").touch()
            self.assertEqual(hashes(root, "00112233", 10), [
                {"file": "ib=00112233.txt"},
                {"file": "log.txt", "line": 2, "text": "hash=00112233"},
            ])

    def test_telemetry(self):
        log = (
            "XXMI_MCP/1 selections pixelshader=0011223344556677 vertexbuffer=ffffffff\n"
            "XXMI_MCP/1 performance begin\nPerformance Monitor 59.9fps\n"
            "XXMI_MCP/1 performance end\n"
        )
        self.assertEqual(selection(log), {"pixelshader": "0011223344556677", "vertexbuffer": None})
        self.assertEqual(performance(log), "Performance Monitor 59.9fps")
        self.assertEqual(frozen_fps(log), 59.9)
        self.assertEqual(marked_hash(">>>> Index buffer marked: index buffer hash = 00112233\n"),
                         {"kind": "Index buffer", "hash": "00112233"})
