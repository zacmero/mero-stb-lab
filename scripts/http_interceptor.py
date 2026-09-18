"""
NET-CONFIG-005: Dual HTTP / HTTPS Multi-Endpoint Server & Interceptor
Handles both plaintext HTTP (8080) and TLS/HTTPS (8443) requests intercepted
from the Sagemcom DSI74 V2 STB.
"""

import sys
import os
import mimetypes
import datetime
import signal
import json
import ssl
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

HTTP_PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
LOG_FILE = sys.argv[2] if len(sys.argv) > 2 else "/home/zacmero/projects/mero-stb-lab/captures/net-config-005.log"
HTTPS_PORT = int(sys.argv[3]) if len(sys.argv) > 3 else 8443

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
REPO_DIR = os.path.dirname(SCRIPT_DIR)
WEB_DIR = os.path.join(REPO_DIR, "web")

CONFIG_FILE = os.path.join(WEB_DIR, "appConfigFit.json")
PORTAL_FILE = os.path.join(WEB_DIR, "portal.html")
PORTAL_SVG = os.path.join(WEB_DIR, "portal.svg")
CERT_FILE = os.path.join(WEB_DIR, "certs", "server.crt")
KEY_FILE = os.path.join(WEB_DIR, "certs", "server.key")

class ConfigServerHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def log_request_details(self):
        now = datetime.datetime.now().isoformat()
        client = f"{self.client_address[0]}:{self.client_address[1]}"
        proto = "HTTPS" if hasattr(self.connection, "cipher") and self.connection.cipher() else "HTTP"
        log_entry = [
            "\n" + "=" * 70,
            f"TIMESTAMP:    {now} [{proto}]",
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
        pass

    def send_safe_response(self, content_bytes, content_type="text/html; charset=utf-8", status=200, extra_headers=None):
        self.send_response(status)
        self.send_header("Server", "gvt-probe")
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Connection", "close")
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, v)
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
            self.send_safe_response(
                redirect_payload,
                content_type="application/json; charset=utf-8",
                extra_headers={"Location": "http://192.168.1.97:8080/portal.html"}
            )
            return

        # Route 1: Application configuration JSON
        if "appConfig" in clean_path or clean_path.endswith(".json"):
            cfg_path = os.path.join(WEB_DIR, "tv-config", "appConfigFit.json")
            if not os.path.exists(cfg_path):
                cfg_path = CONFIG_FILE
            if os.path.exists(cfg_path):
                with open(cfg_path, "rb") as f:
                    content = f.read()
            else:
                content = b'{"status":"ok","code":0}\n'
            self.send_safe_response(content, "application/json; charset=utf-8")
            return

        # Route 1B: Mirada highlights XML
        if "highlights" in clean_path or clean_path.endswith(".xml"):
            hl_file = os.path.join(WEB_DIR, "mirada1-destaques", "highlights_config.xml")
            if not os.path.exists(hl_file):
                hl_file = os.path.join(WEB_DIR, "highlights_config.xml")
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
        content = json.dumps({
            "status": "ok",
            "code": 0,
            "received": True,
            "endpoint": self.path,
            "url": "http://192.168.1.97:8080/portal.html"
        }, indent=2).encode("utf-8")
        self.send_safe_response(content, "application/json; charset=utf-8")

    def do_POST(self):
        self.log_request_details()
        backup_cfg = os.path.join(WEB_DIR, "tv-config", "backupIpConfig.json")
        if not os.path.exists(backup_cfg):
            backup_cfg = os.path.join(WEB_DIR, "backupIpConfig.json")
        if ("backupIpConfig" in self.path or "appConfig" in self.path) and os.path.exists(backup_cfg):
            with open(backup_cfg, "rb") as f:
                content = f.read()
        else:
            content = b'{"status":"ok","code":0,"ack":true}\n'
        self.send_safe_response(content, "application/json; charset=utf-8")

http_server = None
https_server = None

def sigterm_handler(signum, frame):
    global http_server, https_server
    if http_server:
        http_server.server_close()
    if https_server:
        https_server.server_close()
    sys.exit(0)

def run():
    global http_server, https_server
    signal.signal(signal.SIGTERM, sigterm_handler)

    http_server = HTTPServer(("0.0.0.0", HTTP_PORT), ConfigServerHandler)
    print(f"[*] HTTP server listening on  0.0.0.0:{HTTP_PORT}", flush=True)

    if os.path.exists(CERT_FILE) and os.path.exists(KEY_FILE):
        https_server = HTTPServer(("0.0.0.0", HTTPS_PORT), ConfigServerHandler)
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
        https_server.socket = ctx.wrap_socket(https_server.socket, server_side=True)
        print(f"[*] HTTPS server listening on 0.0.0.0:{HTTPS_PORT}", flush=True)
    else:
        print("[-] Warning: TLS certificates not found, HTTPS disabled.", flush=True)

    print(f"[*] Serving config: {CONFIG_FILE}", flush=True)
    print(f"[*] Serving portal: {PORTAL_FILE}", flush=True)
    print(f"[*] Serving SVG:    {PORTAL_SVG}", flush=True)
    print(f"[*] Logging requests to: {LOG_FILE}", flush=True)

    threads = []
    t_http = threading.Thread(target=http_server.serve_forever, daemon=True)
    t_http.start()
    threads.append(t_http)

    if https_server:
        t_https = threading.Thread(target=https_server.serve_forever, daemon=True)
        t_https.start()
        threads.append(t_https)

    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        pass
    finally:
        if http_server:
            http_server.server_close()
        if https_server:
            https_server.server_close()
        print("[*] Dual server shut down cleanly.", flush=True)

if __name__ == "__main__":
    run()
