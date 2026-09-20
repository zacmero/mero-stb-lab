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

            (root / "app-native-018.html").write_bytes(b"<html>probe</html>\n")
            server.profile = "native018"
            status, headers, body = InterfaceHTTPServer.response_for(
                server, "GET", "/bussola/redirect?type=vod"
            )
            self.assertEqual((status, headers["Location"], body), (302, "/app-native-018.html", b""))
            status, _headers, body = InterfaceHTTPServer.response_for(
                server, "GET", "/app-native-018.html"
            )
            self.assertEqual((status, body), (200, b"<html>probe</html>\n"))

            (root / "app-native-018b.xhtml").write_bytes(b"<html>xml probe</html>\n")
            server.profile = "native018b"
            status, headers, body = InterfaceHTTPServer.response_for(
                server, "GET", "/bussola/redirect"
            )
            self.assertEqual((status, headers["Location"], body), (302, "/app-native-018b.xhtml", b""))
            status, headers, body = InterfaceHTTPServer.response_for(
                server, "GET", "/app-native-018b.xhtml"
            )
            self.assertEqual(headers["Content-Type"], "application/xhtml+xml; charset=utf-8")
            self.assertEqual((status, body), (200, b"<html>xml probe</html>\n"))

            (root / "app-native-018c.svg").write_bytes(b"<svg/>\n")
            server.profile = "native018c"
            status, headers, body = InterfaceHTTPServer.response_for(
                server, "GET", "/bussola/redirect"
            )
            self.assertEqual((status, headers["Location"], body), (302, "/app-native-018c.svg", b""))
            status, headers, body = InterfaceHTTPServer.response_for(
                server, "GET", "/app-native-018c.svg"
            )
            self.assertEqual(headers["Content-Type"], "image/svg+xml; charset=utf-8")
            self.assertEqual((status, body), (200, b"<svg/>\n"))

            (root / "app-native-018d.svg").write_bytes(b"<svg>dynamic</svg>\n")
            server.profile = "native018d"
            status, headers, body = InterfaceHTTPServer.response_for(
                server, "GET", "/bussola/redirect"
            )
            self.assertEqual((status, headers["Location"], body), (302, "/app-native-018d.svg", b""))
            status, _headers, body = InterfaceHTTPServer.response_for(
                server, "GET", "/app-native-018d.svg"
            )
            self.assertEqual((status, body), (200, b"<svg>dynamic</svg>\n"))

            (root / "app-native-018e.svg").write_bytes(b"<svg>control</svg>\n")
            server.profile = "native018e"
            status, headers, body = InterfaceHTTPServer.response_for(
                server, "GET", "/bussola/redirect"
            )
            self.assertEqual((status, headers["Location"], body), (302, "/app-native-018e.svg", b""))
            status, _headers, body = InterfaceHTTPServer.response_for(
                server, "GET", "/app-native-018e.svg"
            )
            self.assertEqual((status, body), (200, b"<svg>control</svg>\n"))


if __name__ == "__main__":
    unittest.main()
