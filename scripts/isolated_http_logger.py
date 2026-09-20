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
        record = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "client": self.client_address[0],
            "method": self.command,
            "target": self.path,
            "headers": dict(self.headers.items()),
            "body_length": len(body),
            "body_sha256": hashlib.sha256(body).hexdigest(),
            "body_preview": body[:4096].decode("utf-8", "replace"),
        }
        with self.server.log_path.open("a", encoding="utf-8") as stream:  # type: ignore[attr-defined]
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(f"HTTP {record['timestamp']} {record['client']} {self.command} {self.path}", flush=True)

        response = b"MERO isolated observation: no response configured\n"
        self.send_response(404)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
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
    def __init__(self, address: tuple[str, int], handler: type[Handler], interface: str):
        self.interface = interface
        super().__init__(address, handler, bind_and_activate=False)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, interface.encode() + b"\0")
        self.server_bind()
        self.server_activate()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bind", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=80)
    parser.add_argument("--interface", required=True)
    parser.add_argument("--log", type=Path, required=True)
    args = parser.parse_args()
    server = InterfaceHTTPServer((args.bind, args.port), Handler, args.interface)
    server.log_path = args.log
    print(f"HTTP logger listening on {args.interface} {args.bind}:{args.port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
