#!/usr/bin/env python3
"""Log receiver HTTP requests on an isolated Ethernet link and return 404."""

import argparse
import hashlib
import http.server
import json
import socket
import time
from pathlib import Path


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _handle(self) -> None:
        length = min(int(self.headers.get("Content-Length", "0") or 0), 1_048_576)
        body = self.rfile.read(length) if length else b""
        status, response_headers, response = self.server.response_for(  # type: ignore[attr-defined]
            self.command, self.path
        )
        record = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "client": self.client_address[0],
            "method": self.command,
            "target": self.path,
            "headers": dict(self.headers.items()),
            "body_length": len(body),
            "body_sha256": hashlib.sha256(body).hexdigest(),
            "body_preview": body[:4096].decode("utf-8", "replace"),
            "response_status": status,
            "response_length": len(response),
            "profile": self.server.profile,  # type: ignore[attr-defined]
        }
        with self.server.log_path.open("a", encoding="utf-8") as stream:  # type: ignore[attr-defined]
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(
            f"HTTP {record['timestamp']} {record['client']} {self.command} "
            f"{self.path} -> {status}",
            flush=True,
        )

        self.send_response(status)
        for name, value in response_headers.items():
            self.send_header(name, value)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(response)))
        self.send_header("Connection", "close")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(response)

    do_GET = do_POST = do_PUT = do_DELETE = do_HEAD = do_OPTIONS = _handle

    def log_message(self, _format: str, *_args: object) -> None:
        return


class InterfaceHTTPServer(http.server.ThreadingHTTPServer):
    def __init__(
        self,
        address: tuple[str, int],
        handler: type[Handler],
        interface: str,
        profile: str,
        asset_root: Path,
    ):
        self.interface = interface
        self.profile = profile
        self.asset_root = asset_root
        super().__init__(address, handler, bind_and_activate=False)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, interface.encode() + b"\0")
        self.server_bind()
        self.server_activate()

    def response_for(self, method: str, target: str) -> tuple[int, dict[str, str], bytes]:
        path = target.split("?", 1)[0]
        if self.profile in ("baseline", "native018", "native018b", "native018c", "native018d", "native018e"):
            if path == "/":
                return 200, {"Content-Type": "text/plain; charset=utf-8"}, b"OK\n"
            if self.profile == "native018" and path == "/bussola/redirect":
                return 302, {"Content-Type": "text/plain", "Location": "/app-native-018.html"}, b""
            if self.profile == "native018" and path == "/app-native-018.html":
                return (
                    200,
                    {"Content-Type": "text/html; charset=utf-8"},
                    (self.asset_root / "app-native-018.html").read_bytes(),
                )
            if self.profile == "native018b" and path == "/bussola/redirect":
                return 302, {"Content-Type": "text/plain", "Location": "/app-native-018b.xhtml"}, b""
            if self.profile == "native018b" and path == "/app-native-018b.xhtml":
                return (
                    200,
                    {"Content-Type": "application/xhtml+xml; charset=utf-8"},
                    (self.asset_root / "app-native-018b.xhtml").read_bytes(),
                )
            if self.profile == "native018c" and path == "/bussola/redirect":
                return 302, {"Content-Type": "text/plain", "Location": "/app-native-018c.svg"}, b""
            if self.profile == "native018c" and path == "/app-native-018c.svg":
                return (
                    200,
                    {"Content-Type": "image/svg+xml; charset=utf-8"},
                    (self.asset_root / "app-native-018c.svg").read_bytes(),
                )
            if self.profile == "native018d" and path == "/bussola/redirect":
                return 302, {"Content-Type": "text/plain", "Location": "/app-native-018d.svg"}, b""
            if self.profile == "native018d" and path == "/app-native-018d.svg":
                return (
                    200,
                    {"Content-Type": "image/svg+xml; charset=utf-8"},
                    (self.asset_root / "app-native-018d.svg").read_bytes(),
                )
            if self.profile == "native018e" and path == "/bussola/redirect":
                return 302, {"Content-Type": "text/plain", "Location": "/app-native-018e.svg"}, b""
            if self.profile == "native018e" and path == "/app-native-018e.svg":
                return (
                    200,
                    {"Content-Type": "image/svg+xml; charset=utf-8"},
                    (self.asset_root / "app-native-018e.svg").read_bytes(),
                )
            if self.profile in ("native018", "native018b", "native018c", "native018d", "native018e") and path == "/app-native-018/report":
                return 200, {"Content-Type": "text/plain"}, b"OK\n"
            routes = {
                "/mirada1-destaques/highlights_config.xml": (
                    "mirada1-destaques/highlights_config.xml",
                    "application/xml; charset=utf-8",
                ),
                "/tv-config/appConfigFit.json": (
                    "tv-config/appConfigFit.json",
                    "application/json; charset=utf-8",
                ),
            }
            if path in routes:
                relative, content_type = routes[path]
                return 200, {"Content-Type": content_type}, (self.asset_root / relative).read_bytes()
            if path == "/tv-config/backupIpConfig.json":
                return (
                    200,
                    {"Content-Type": "application/json; charset=utf-8"},
                    b'{"status":"ok","code":0,"ack":true}\n',
                )
            if path.startswith("/paytv-stats"):
                return 200, {"Content-Type": "application/json"}, b'{"status":"ok","code":0}\n'
        return (
            404,
            {"Content-Type": "text/plain; charset=utf-8"},
            b"MERO isolated observation: no response configured\n",
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bind", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=80)
    parser.add_argument("--interface", required=True)
    parser.add_argument(
        "--profile",
        choices=("observe", "baseline", "native018", "native018b", "native018c", "native018d", "native018e"),
        default="observe",
    )
    parser.add_argument("--asset-root", type=Path, default=Path.cwd())
    parser.add_argument("--log", type=Path, required=True)
    args = parser.parse_args()
    server = InterfaceHTTPServer(
        (args.bind, args.port), Handler, args.interface, args.profile, args.asset_root
    )
    server.log_path = args.log
    print(
        f"HTTP logger listening on {args.interface} {args.bind}:{args.port} "
        f"profile={args.profile}",
        flush=True,
    )
    server.serve_forever()


if __name__ == "__main__":
    main()
