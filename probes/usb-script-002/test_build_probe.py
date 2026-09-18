"""Host-only tests: do not open USB drives or communicate with the receiver."""
import contextlib
import hashlib
import io
from pathlib import Path
import tempfile
import unittest

import build_probe as probe

HERE = Path(__file__).resolve().parent


class ProbeTests(unittest.TestCase):
    def setUp(self):
        self.source = probe.script_text("192.168.1.97", "192.168.1.134", "255.255.255.0")
        self.image = probe.encode_script(self.source)

    def test_round_trip(self):
        self.assertEqual(probe.decode_script(self.image), self.source)
        probe.audit_script(self.source)

    def test_shipped_images_match_builder(self):
        for name in probe.TARGETS:
            with self.subTest(name=name):
                self.assertEqual((HERE / "prepared/usb-files" / name).read_bytes(), self.image)

    def test_header_crc_rejects_corruption(self):
        damaged = bytearray(self.image)
        damaged[8] ^= 1
        with self.assertRaises(ValueError):
            probe.decode_script(bytes(damaged))

    def test_payload_crc_rejects_corruption(self):
        damaged = bytearray(self.image)
        damaged[-2] ^= 1
        with self.assertRaises(ValueError):
            probe.decode_script(bytes(damaged))

    def test_truncation_is_rejected(self):
        for size in (0, 63, 71, len(self.image) - 1):
            with self.subTest(size=size), self.assertRaises(ValueError):
                probe.decode_script(self.image[:size])

    def test_persistent_or_raw_write_commands_are_rejected(self):
        for command in ("saveenv", "nand erase", "sf write 0 0 4", "mw 0 1", "reset"):
            with self.subTest(command=command), self.assertRaises(ValueError):
                probe.audit_script(self.source + command + "\n")

    def test_invalid_address_pairs_are_rejected(self):
        for pc, box in (("192.168.1.97", "192.168.1.97"),
                        ("192.168.2.97", "192.168.1.134"),
                        ("192.168.1.255", "192.168.1.134"),
                        ("127.0.0.1", "127.0.0.2")):
            with self.subTest(pc=pc, box=box), self.assertRaises(ValueError):
                probe.validate_addresses(pc, box, "255.255.255.0")

    def test_rebuild_is_reproducible_and_existing_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "prepared"
            with contextlib.redirect_stdout(io.StringIO()):
                probe.write_bundle(out, "192.168.1.97", "192.168.1.134", "255.255.255.0")
                probe.verify_bundle(out)
            original = out / "usb-files/boot.scr"
            self.assertEqual(original.read_bytes(), self.image)
            with self.assertRaises(ValueError):
                probe.write_bundle(out, "192.168.1.97", "192.168.1.134", "255.255.255.0")
            self.assertEqual(original.read_bytes(), self.image)

    def test_all_shipped_checksums(self):
        base = HERE / "prepared"
        for line in (base / "SHA256SUMS").read_text().splitlines():
            expected, name = line.split("  ", 1)
            with self.subTest(name=name):
                self.assertEqual(hashlib.sha256((base / name).read_bytes()).hexdigest(), expected)

    def test_shipped_bundle_verifies(self):
        with contextlib.redirect_stdout(io.StringIO()):
            probe.verify_bundle(HERE / "prepared")


if __name__ == "__main__":
    unittest.main()
