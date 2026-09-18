#!/usr/bin/env python3
"""
NET-PROVISION-004: HTTP Interceptor & Request Logger (Flushed & Unbuffered)
Listens on local port, completes TCP handshakes, logs raw HTTP requests,
and answers HEAD / GET requests with immediate 200 OK.
"""

import sys
import datetime
import signal
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
LOG_FILE = sys.argv[2] if len(sys.argv) > 2 else "/home/zacmero/projects/mero-stb-lab/captures/net-provision-004.log"

class LoggingHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def log_request_details(self):
        now = datetime.datetime.now().isoformat()
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length > 0 else b""

        log_lines = [
            f"\n{'='*70}",
            f"TIMESTAMP:    {now}",
            f"CLIENT:       {self.client_address[0]}:{self.client_address[1]}",
            f"REQUEST:      {self.command} {self.path} {self.request_version}",
            "--- HEADERS ---",
        ]
        for key, value in self.headers.items():
            log_lines.append(f"  {key}: {value}")

        if body:
            log_lines.append("--- BODY ---")
            try:
                log_lines.append(body.decode("utf-8", errors="replace"))
            except Exception:
                log_lines.append(f"<binary data {len(body)} bytes>")

        log_lines.append(f"{'='*70}\n")
        output = "\n".join(log_lines)

        print(output, flush=True)
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(output)
                f.flush()
        except Exception as e:
            print(f"[!] Error writing log: {e}", file=sys.stderr, flush=True)

    def do_HEAD(self):
        self.log_request_details()
        self.send_response(200)
        self.send_header("Server", "gvt-probe")
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", "0")
        self.send_header("Connection", "close")
        self.end_headers()

    def do_GET(self):
        self.log_request_details()
        self.send_response(200)
        self.send_header("Server", "gvt-probe")
        self.send_header("Content-Type", "application/json")
        self.send_header("Connection", "close")
        response = b'{"status":"ok","code":0}\n'
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def do_POST(self):
        self.log_request_details()
        self.send_response(200)
        self.send_header("Server", "gvt-probe")
        self.send_header("Content-Type", "application/json")
        self.send_header("Connection", "close")
        response = b'{"status":"ok","code":0}\n'
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

server = None
def sigterm_handler(signum, frame):
    global server
    if server:
        server.server_close()
    sys.exit(0)

def run():
    global server
    signal.signal(signal.SIGTERM, sigterm_handler)
    server = HTTPServer(("0.0.0.0", PORT), LoggingHandler)
    print(f"[*] HTTP Interceptor listening on 0.0.0.0:{PORT}", flush=True)
    print(f"[*] Logging requests to: {LOG_FILE}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        print("[*] HTTP Interceptor shut down cleanly.", flush=True)

if __name__ == "__main__":
    run()
