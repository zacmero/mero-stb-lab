#!/usr/bin/env python3
import tempfile
import unittest
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))

from isolated_http_logger import InterfaceHTTPServer  # noqa: E402


class ResponseProfileTest(unittest.TestCase):
    def test_baseline_serves_only_known_routes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "tv-config").mkdir()
            (root / "mirada1-destaques").mkdir()
            (root / "tv-config/appConfigFit.json").write_bytes(b'{"version":"test"}\n')
            (root / "mirada1-destaques/highlights_config.xml").write_bytes(b"<highlights/>\n")
            server = SimpleNamespace(profile="baseline", asset_root=root)

            status, _headers, body = InterfaceHTTPServer.response_for(
                server, "GET", "/tv-config/appConfigFit.json?ignored=1"
            )
            self.assertEqual((status, body), (200, b'{"version":"test"}\n'))
            status, _headers, body = InterfaceHTTPServer.response_for(
                server, "POST", "/tv-config/backupIpConfig.json"
            )
            self.assertEqual(
                (status, body),
                (200, b'{"status":"ok","code":0,"ack":true}\n'),
            )
            status, _headers, _body = InterfaceHTTPServer.response_for(
                server, "GET", "/unknown-update.bin"
            )
            self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
