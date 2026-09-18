"""
NET-CONFIG-005: Multi-Endpoint HTTP Server & Interceptor
Routes configuration JSON, serves diagnostic portal (HTML/SVG), and logs all
subsequent asset/API queries from the Ekioh embedded browser.
"""

import sys
import os
import mimetypes
import datetime
import signal
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
LOG_FILE = sys.argv[2] if len(sys.argv) > 2 else "/home/zacmero/projects/mero-stb-lab/captures/net-config-005.log"

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
REPO_DIR = os.path.dirname(SCRIPT_DIR)
WEB_DIR = os.path.join(REPO_DIR, "web")

CONFIG_FILE = os.path.join(WEB_DIR, "appConfigFit.json")
PORTAL_FILE = os.path.join(WEB_DIR, "portal.html")
PORTAL_SVG = os.path.join(WEB_DIR, "portal.svg")

class ConfigServerHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def log_request_details(self):
        now = datetime.datetime.now().isoformat()
        client = f"{self.client_address[0]}:{self.client_address[1]}"
        log_entry = [
            "\n" + "=" * 70,
            f"TIMESTAMP:    {now}",
            f"CLIENT:       {client}",
            f"REQUEST:      {self.command} {self.path} {self.request_version}",
            "--- HEADERS ---",
        ]
        for header, val in self.headers.items():
            log_entry.append(f"  {header}: {val}")
        log_entry.append("=" * 70 + "\n")

        formatted = "\n".join(log_entry)
        print(formatted, flush=True)

        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(formatted)
                f.flush()
                os.fsync(f.fileno())
        except Exception as e:
            print(f"[-] Error writing to log: {e}", flush=True)

    def log_message(self, format, *args):
        # Override default stderr logging to keep output clean and controlled
        pass

    def send_safe_response(self, content_bytes, content_type="text/html; charset=utf-8", status=200):
        self.send_response(status)
        self.send_header("Server", "gvt-probe")
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(content_bytes)

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

        clean_path = self.path.split("?")[0].lstrip("/")

        # Route 0: Bussola / Interactive VOD redirect
        if "bussola" in clean_path or "redirect" in clean_path:
            redirect_dict = {
                "status": "ok",
                "code": 0,
                "url": "http://192.168.1.97:8080/portal.html",
                "redirect": "http://192.168.1.97:8080/portal.html",
                "redirectUrl": "http://192.168.1.97:8080/portal.html",
                "portalUrl": "http://192.168.1.97:8080/portal.html",
                "vodUrl": "http://192.168.1.97:8080/portal.html",
                "target": "http://192.168.1.97:8080/portal.html",
                "location": "http://192.168.1.97:8080/portal.html",
                "destination": "http://192.168.1.97:8080/portal.html",
                "result": {
                    "url": "http://192.168.1.97:8080/portal.html",
                    "status": "ok"
                },
                "data": {
                    "url": "http://192.168.1.97:8080/portal.html"
                }
            }
            redirect_payload = json.dumps(redirect_dict, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Server", "gvt-probe")
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Location", "http://192.168.1.97:8080/portal.html")
            self.send_header("Content-Length", str(len(redirect_payload)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(redirect_payload)
            return

        # Route 1: Application configuration JSON
        if "appConfig" in clean_path or clean_path.endswith(".json"):
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "rb") as f:
                    content = f.read()
            else:
                content = b'{"status":"ok","code":0}\n'
            self.send_safe_response(content, "application/json; charset=utf-8")
            return

        # Route 1B: Mirada highlights XML
        if "highlights" in clean_path or clean_path.endswith(".xml"):
            hl_file = os.path.join(WEB_DIR, "mirada1-destaques", "highlights_config.xml")
            if os.path.exists(hl_file):
                with open(hl_file, "rb") as f:
                    content = f.read()
            else:
                content = b'<?xml version="1.0" encoding="utf-8"?><highlights><highlight id="1"><title>HELLO FROM THE GH05T</title></highlight></highlights>'
            self.send_safe_response(content, "application/xml; charset=utf-8")
            return

        # Route 2: Static file from web/ directory if it exists
        local_target = os.path.join(WEB_DIR, clean_path)
        if clean_path and os.path.isfile(local_target):
            mime, _ = mimetypes.guess_type(local_target)
            if not mime:
                mime = "text/plain; charset=utf-8"
            elif mime.startswith("text/") or mime in ("application/javascript", "image/svg+xml", "application/xml"):
                mime += "; charset=utf-8"
            with open(local_target, "rb") as f:
                content = f.read()
            self.send_safe_response(content, mime)
            return

        # Route 3: Diagnostic portal SVG
        if "svg" in clean_path or clean_path.endswith(".svg"):
            if os.path.exists(PORTAL_SVG):
                with open(PORTAL_SVG, "rb") as f:
                    content = f.read()
            else:
                content = b'<svg><text>HELLO FROM THE GH05T</text></svg>'
            self.send_safe_response(content, "image/svg+xml; charset=utf-8")
            return

        # Route 4: Diagnostic portal HTML (default for root / portal queries)
        if "portal" in clean_path or clean_path == "" or clean_path.endswith(".html"):
            if os.path.exists(PORTAL_FILE):
                with open(PORTAL_FILE, "rb") as f:
                    content = f.read()
            else:
                content = b"<!DOCTYPE html><html><body><h1>HELLO FROM THE GH05T</h1></body></html>"
            self.send_safe_response(content, "text/html; charset=utf-8")
            return

        # Route 5: Catch-all fallback for unknown paths
        content = b'{"status":"ok","received":true,"endpoint":"' + self.path.encode("utf-8") + b'"}\n'
        self.send_safe_response(content, "application/json; charset=utf-8")

    def do_POST(self):
        self.log_request_details()
        backup_cfg = os.path.join(WEB_DIR, "tv-config", "backupIpConfig.json")
        if "backupIpConfig" in self.path and os.path.exists(backup_cfg):
            with open(backup_cfg, "rb") as f:
                content = f.read()
        else:
            content = b'{"status":"ok","ack":true}\n'
        self.send_safe_response(content, "application/json; charset=utf-8")

server = None
def sigterm_handler(signum, frame):
    global server
    if server:
        server.server_close()
    sys.exit(0)

def run():
    global server
    signal.signal(signal.SIGTERM, sigterm_handler)
    server = HTTPServer(("0.0.0.0", PORT), ConfigServerHandler)
    print(f"[*] NET-CONFIG-005 server listening on 0.0.0.0:{PORT}", flush=True)
    print(f"[*] Serving config: {CONFIG_FILE}", flush=True)
    print(f"[*] Serving portal: {PORTAL_FILE}", flush=True)
    print(f"[*] Serving SVG:    {PORTAL_SVG}", flush=True)
    print(f"[*] Logging requests to: {LOG_FILE}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        print("[*] Server shut down cleanly.", flush=True)

if __name__ == "__main__":
    run()
