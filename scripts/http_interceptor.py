"""
MERO-STB-LAB: Differential HTTP/HTTPS Interceptor & Experiment Harness
Implements exact Host+Method+Path+Query routing, bounded request body capture,
cryptographic SHA-256 body hashing, source classification (LOCAL_SELFTEST vs RECEIVER_HW),
and dynamic test case management.
"""

import sys
import os
import time
import json
import hashlib
import urllib.parse
import ssl
import signal
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

HTTP_PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
LOG_FILE = sys.argv[2] if len(sys.argv) > 2 else "/home/zacmero/projects/mero-stb-lab/captures/net-config-005.log"
HTTPS_PORT = int(sys.argv[3]) if len(sys.argv) > 3 else 8443

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
REPO_DIR = os.path.dirname(SCRIPT_DIR)
CAPTURES_DIR = os.path.join(REPO_DIR, "captures")
JSONL_LOG = os.path.join(CAPTURES_DIR, "experiment_transactions.jsonl")
CASE_FILE = "/tmp/mero_active_case.json"

TARGET_MAC = "68:15:90:6b:81:96"
CERT_FILE = os.path.join(REPO_DIR, "web", "certs", "server.crt")
KEY_FILE = os.path.join(REPO_DIR, "web", "certs", "server.key")

# Global active case state
CURRENT_CASE = {
    "case_id": "CASE-00-BASELINE",
    "description": "Repeatable baseline - minimal JSON, no navigation fields, no redirects",
    "bussola_status": 200,
    "bussola_headers": {"Content-Type": "application/json; charset=utf-8"},
    "bussola_body": json.dumps({"status": "ok", "code": 0}),
    "appconfig_status": 200,
    "appconfig_headers": {"Content-Type": "application/json; charset=utf-8"},
    "appconfig_body": json.dumps({"status": "ok", "code": 0}),
}
CASE_LOCK = threading.Lock()

def get_active_case():
    with CASE_LOCK:
        if os.path.exists(CASE_FILE):
            try:
                with open(CASE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data
            except Exception:
                pass
        return dict(CURRENT_CASE)

def set_active_case(case_dict):
    with CASE_LOCK:
        CURRENT_CASE.clear()
        CURRENT_CASE.update(case_dict)
        try:
            with open(CASE_FILE, "w", encoding="utf-8") as f:
                json.dump(case_dict, f, indent=2)
        except Exception as e:
            print(f"[-] Error writing case file: {e}", flush=True)

def classify_client(client_ip):
    if client_ip in ("127.0.0.1", "::1", "192.168.1.97"):
        return "LOCAL_SELFTEST"
    # Check ARP cache
    try:
        with open("/proc/net/arp", "r") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 4 and parts[0] == client_ip:
                    if parts[3].lower() == TARGET_MAC.lower():
                        return "RECEIVER_HW"
    except Exception:
        pass
    return "LAN_OTHER"

class DifferentialHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def read_bounded_body(self, max_bytes=65536, timeout=2.0):
        length_header = self.headers.get("Content-Length")
        if not length_header:
            return b""
        try:
            length = int(length_header)
        except ValueError:
            return b""
        if length <= 0:
            return b""
        read_size = min(length, max_bytes)
        self.connection.settimeout(timeout)
        try:
            body = self.rfile.read(read_size)
            return body
        except Exception:
            return b""

    def record_transaction(self, method, raw_path, req_body, resp_status, resp_headers, resp_body, case_id):
        now = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + f".{int((time.time()%1)*1e6):06d}Z"
        client_ip = self.client_address[0]
        client_port = self.client_address[1]
        source = classify_client(client_ip)
        host = self.headers.get("Host", "").split(":")[0].strip()

        req_hash = hashlib.sha256(req_body).hexdigest() if req_body else None
        resp_hash = hashlib.sha256(resp_body).hexdigest() if resp_body else None

        record = {
            "timestamp": now,
            "source": source,
            "case_id": case_id,
            "run_id": get_active_case().get("run_id"),
            "client": f"{client_ip}:{client_port}",
            "method": method,
            "host": host,
            "path": raw_path,
            "headers": dict(self.headers),
            "request_body_size": len(req_body),
            "request_body_sha256": req_hash,
            "request_body_snippet": req_body[:512].decode("latin1", errors="replace") if req_body else "",
            "response_http_version": getattr(self, "protocol_version", "HTTP/1.1"),
            "response_status": resp_status,
            "response_headers": resp_headers,
            "response_body_size": len(resp_body),
            "response_body_sha256": resp_hash,
        }

        # Write to JSONL
        try:
            with open(JSONL_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
                f.flush()
        except Exception as e:
            print(f"[-] JSONL write error: {e}", flush=True)

        # Write to human log
        proto = "HTTPS" if hasattr(self.connection, "cipher") and self.connection.cipher() else "HTTP"
        lines = [
            f"\n{'='*70}",
            f"TIMESTAMP:    {now} [{proto}] [{source}] Case: {case_id}",
            f"CLIENT:       {client_ip}:{client_port} (Host: {host})",
            f"REQUEST:      {method} {raw_path}",
            f"RESPONSE:     {getattr(self, 'protocol_version', 'HTTP/1.1')} {resp_status} ({len(resp_body)} B, SHA256: {resp_hash[:16] if resp_hash else 'none'}...)"
        ]
        if req_body:
            lines.append(f"REQ_BODY ({len(req_body)} B): {req_body[:256].decode('latin1', errors='replace')}")
        lines.append(f"{'='*70}\n")
        formatted = "\n".join(lines)
        print(formatted, flush=True)
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(formatted)
                f.flush()
        except Exception:
            pass

    def send_exact_response(self, status, headers_dict, body_bytes, case_id):
        active_case = get_active_case()
        proto_ver = active_case.get("http_version")
        if proto_ver:
            self.protocol_version = proto_ver
        else:
            self.protocol_version = "HTTP/1.1"

        self.send_response(status)
        server_val = active_case.get("server_header", "mero-harness/1.0")
        sent_headers = {
            "Server": server_val,
            "Content-Length": str(len(body_bytes))
        }
        self.send_header("Server", server_val)
        self.send_header("Content-Length", str(len(body_bytes)))
        if "Connection" not in headers_dict:
            self.send_header("Connection", "close")
            sent_headers["Connection"] = "close"
        for k, v in headers_dict.items():
            self.send_header(k, v)
            sent_headers[k] = v
        self.end_headers()
        self.wfile.write(body_bytes)
        return status, sent_headers, body_bytes

    def handle_route(self, method):
        parsed = urllib.parse.urlsplit(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)
        host = self.headers.get("Host", "").split(":")[0].strip()
        req_body = self.read_bounded_body()
        active_case = get_active_case()
        case_id = active_case.get("case_id", "BASELINE")

        # -------------------------------------------------------------
        # Admin / Harness Dynamic Control Endpoint
        # -------------------------------------------------------------
        if path == "/_harness/set_case" and method == "POST":
            try:
                new_case = json.loads(req_body.decode("utf-8"))
                set_active_case(new_case)
                resp = json.dumps({"status": "ok", "active_case": new_case}).encode("utf-8")
                self.send_exact_response(200, {"Content-Type": "application/json"}, resp, case_id)
                self.record_transaction(method, self.path, req_body, 200, {"Content-Type": "application/json"}, resp, case_id)
                return
            except Exception as e:
                resp = json.dumps({"error": str(e)}).encode("utf-8")
                self.send_exact_response(400, {"Content-Type": "application/json"}, resp, case_id)
                self.record_transaction(method, self.path, req_body, 400, {"Content-Type": "application/json"}, resp, case_id)
                return

        if path == "/_harness/get_case" and method == "GET":
            resp = json.dumps(active_case).encode("utf-8")
            self.send_exact_response(200, {"Content-Type": "application/json"}, resp, case_id)
            self.record_transaction(method, self.path, req_body, 200, {"Content-Type": "application/json"}, resp, case_id)
            return

        # -------------------------------------------------------------
        # Route 1: Marker Endpoints (/marker/<id>)
        # Critical evidence: If client requests this, a candidate was followed!
        # -------------------------------------------------------------
        if path.startswith("/marker/"):
            marker_name = path[len("/marker/"):]
            client_ip = self.client_address[0]
            src = classify_client(client_ip)
            print(f"\n[*** EVIDENCE HIT ***] MARKER FETCHED: {marker_name} by {client_ip} ({src}) in Case {case_id}!\n", flush=True)
            
            if marker_name.endswith(".png"):
                body = (
                    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
                    b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00"
                    b"\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82"
                )
                headers = {"Content-Type": "image/png"}
            else:
                body = (
                    '<?xml version="1.0" encoding="UTF-8"?>\n'
                    '<svg xmlns="http://www.w3.org/2000/svg" version="1.2" baseProfile="tiny" width="1280" height="720">\n'
                    '  <rect width="1280" height="720" fill="#050811" />\n'
                    f'  <text x="640" y="360" fill="#00ffcc" font-family="sans-serif" font-size="36" text-anchor="middle">MARKER HIT: {marker_name}</text>\n'
                    '  <script type="text/ecmascript"><![CDATA[\n'
                    '    try {\n'
                    '      var xhr = new XMLHttpRequest();\n'
                    f'      xhr.open("GET", "/report/script_exec?marker={marker_name}&run=" + (20+22), true);\n'
                    '      xhr.send();\n'
                    '    } catch(e) {}\n'
                    '  ]]></script>\n'
                    '</svg>\n'
                ).encode("utf-8")
                headers = {"Content-Type": "image/svg+xml; charset=utf-8"}
            self.send_exact_response(200, headers, body, case_id)
            self.record_transaction(method, self.path, req_body, 200, headers, body, case_id)
            return

        # -------------------------------------------------------------
        # Route 1b: Portal SVG (/portal.svg)
        # Critical evidence for CASE-12-HISTORICAL-PORTAL
        # -------------------------------------------------------------
        if path == "/portal.svg":
            client_ip = self.client_address[0]
            src = classify_client(client_ip)
            print(f"\n[*** EVIDENCE HIT ***] /portal.svg FETCHED by {client_ip} ({src}) in Case {case_id}!\n", flush=True)
            portal_file = os.path.join(REPO_DIR, "web", "portal.svg")
            if os.path.exists(portal_file):
                with open(portal_file, "rb") as f:
                    body = f.read()
            else:
                body = (
                    '<?xml version="1.0" encoding="UTF-8"?>\n'
                    '<svg xmlns="http://www.w3.org/2000/svg" version="1.2" baseProfile="tiny" width="1280" height="720">\n'
                    '  <rect width="1280" height="720" fill="#0b0f19" />\n'
                    '  <text x="640" y="360" fill="#00ffcc" font-family="sans-serif" font-size="36" text-anchor="middle">PORTAL SVG DELIVERED</text>\n'
                    '</svg>\n'
                ).encode("utf-8")
            headers = {"Content-Type": "image/svg+xml; charset=utf-8"}
            self.send_exact_response(200, headers, body, case_id)
            self.record_transaction(method, self.path, req_body, 200, headers, body, case_id)
            return

        # -------------------------------------------------------------
        # Route 1c: Render Probe SVG (/probe.svg)
        # Tests SVG sub-resource resolution and script execution
        # -------------------------------------------------------------
        if path == "/probe.svg":
            client_ip = self.client_address[0]
            src = classify_client(client_ip)
            print(f"\n[*** EVIDENCE HIT ***] /probe.svg FETCHED by {client_ip} ({src}) in Case {case_id}!\n", flush=True)
            body = (
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.2" baseProfile="tiny" width="1280" height="720">\n'
                '  <rect width="1280" height="720" fill="#050811" />\n'
                '  <text x="640" y="300" fill="#00ffcc" font-family="sans-serif" font-size="36" text-anchor="middle">MERO-STB-LAB: RENDER PROBE</text>\n'
                '  <image xlink:href="http://191.32.31.251/marker/probe_subresource.png" width="50" height="50" x="10" y="10" />\n'
                '  <script type="text/ecmascript"><![CDATA[\n'
                '    try {\n'
                '      if (window.getURL) window.getURL("http://191.32.31.251/report/script_exec?method=getURL", function(){});\n'
                '    } catch(e) {}\n'
                '    try {\n'
                '      var xhr = new XMLHttpRequest();\n'
                '      xhr.open("GET", "http://191.32.31.251/report/script_exec?method=xhr", true);\n'
                '      xhr.send();\n'
                '    } catch(e) {}\n'
                '  ]]></script>\n'
                '</svg>\n'
            ).encode("utf-8")
            headers = {"Content-Type": "image/svg+xml; charset=utf-8"}
            self.send_exact_response(200, headers, body, case_id)
            self.record_transaction(method, self.path, req_body, 200, headers, body, case_id)
            return

        # -------------------------------------------------------------
        # Route 2: Script Execution Callback (/report/script_exec)
        # Demonstrates actual JavaScript execution
        # -------------------------------------------------------------
        if path.startswith("/report/"):
            client_ip = self.client_address[0]
            src = classify_client(client_ip)
            print(f"\n[*** CRITICAL HIT ***] SCRIPT EXECUTION DEMONSTRATED! Path={self.path} by {client_ip} ({src})!\n", flush=True)
            body = b'{"status":"acknowledged","script_executed":true}\n'
            headers = {"Content-Type": "application/json"}
            self.send_exact_response(200, headers, body, case_id)
            self.record_transaction(method, self.path, req_body, 200, headers, body, case_id)
            return

        # -------------------------------------------------------------
        # Route 3: Bussola / Interactive Redirect (/bussola/redirect)
        # Host: 191.32.31.251 (or localhost / PC during test)
        # -------------------------------------------------------------
        if path == "/bussola/redirect":
            if host in ("191.32.31.251", "127.0.0.1", "192.168.1.97", ""):
                status = active_case.get("bussola_status", 200)
                headers = dict(active_case.get("bussola_headers", {"Content-Type": "application/json; charset=utf-8"}))
                body = active_case.get("bussola_body", '{"status":"ok","code":0}').encode("utf-8")
                status, sent_hdrs, body = self.send_exact_response(status, headers, body, case_id)
                self.record_transaction(method, self.path, req_body, status, sent_hdrs, body, case_id)
                return

        # -------------------------------------------------------------
        # Route 4: Application Configuration (/tv-config/appConfigFit.json)
        # Host: 191.32.31.251 (or localhost / PC during test)
        # -------------------------------------------------------------
        if path == "/tv-config/appConfigFit.json":
            if host in ("191.32.31.251", "127.0.0.1", "192.168.1.97", ""):
                status = active_case.get("appconfig_status", 200)
                headers = dict(active_case.get("appconfig_headers", {"Content-Type": "application/json; charset=utf-8"}))
                body = active_case.get("appconfig_body", '{"status":"ok","code":0}').encode("utf-8")
                self.send_exact_response(status, headers, body, case_id)
                self.record_transaction(method, self.path, req_body, status, headers, body, case_id)
                return

        # -------------------------------------------------------------
        # Route 5: Backup IP Configuration (/tv-config/backupIpConfig.json)
        # Dispatched by curl/7.32.0 on STB
        # -------------------------------------------------------------
        if path == "/tv-config/backupIpConfig.json" and method == "POST":
            if host in ("191.32.31.251", "127.0.0.1", "192.168.1.97", ""):
                body = b'{"status":"ok","code":0,"ack":true}\n'
                headers = {"Content-Type": "application/json; charset=utf-8"}
                self.send_exact_response(200, headers, body, case_id)
                self.record_transaction(method, self.path, req_body, 200, headers, body, case_id)
                return

        # -------------------------------------------------------------
        # Route 6: Mirada Highlights XML (/mirada1-destaques/highlights_config.xml)
        # Host: 186.215.183.217
        # -------------------------------------------------------------
        if path == "/mirada1-destaques/highlights_config.xml":
            if host in ("186.215.183.217", "127.0.0.1", "192.168.1.97", ""):
                body = (
                    '<?xml version="1.0" encoding="utf-8"?>\n'
                    '<highlights version="1.0">\n'
                    '  <highlight id="1" name="DIAGNOSTIC TEST">\n'
                    '    <title>MERO-STB LAB</title>\n'
                    '    <channel>DIFF TEST</channel>\n'
                    '    <description>Mero STB Lab Diagnostic</description>\n'
                    '    <url>/marker/highlight_url</url>\n'
                    '  </highlight>\n'
                    '</highlights>\n'
                ).encode("utf-8")
                headers = {"Content-Type": "application/xml; charset=utf-8"}
                self.send_exact_response(200, headers, body, case_id)
                self.record_transaction(method, self.path, req_body, 200, headers, body, case_id)
                return

        # -------------------------------------------------------------
        # Route 7: Social / Facebook App Mock
        # Host: 177.135.68.178
        # -------------------------------------------------------------
        if path in ("/facebook/login", "/facebook/verifycode"):
            if host in ("177.135.68.178", "127.0.0.1", "192.168.1.97", ""):
                if "verifycode" in path:
                    body = json.dumps({"status": "success", "authenticated": True, "code": "GH05T"}).encode("utf-8")
                else:
                    body = json.dumps({"status": "success", "code": "GH05T", "user_code": "GH05T", "url": "/marker/fb_url"}).encode("utf-8")
                headers = {"Content-Type": "application/json; charset=utf-8"}
                self.send_exact_response(200, headers, body, case_id)
                self.record_transaction(method, self.path, req_body, 200, headers, body, case_id)
                return

        # -------------------------------------------------------------
        # Route 8: PayTV Telemetry Register (/paytv-stats-web/api/event/register)
        # Host: 186.215.183.216
        # -------------------------------------------------------------
        if path == "/paytv-stats-web/api/event/register" and method == "POST":
            if host in ("186.215.183.216", "127.0.0.1", "192.168.1.97", ""):
                body = b'{"status":"ok","code":0,"ack":true}\n'
                headers = {"Content-Type": "application/json; charset=utf-8"}
                self.send_exact_response(200, headers, body, case_id)
                self.record_transaction(method, self.path, req_body, 200, headers, body, case_id)
                return

        # -------------------------------------------------------------
        # Route 9: Explicit 404 for any unmapped route or host mismatch
        # -------------------------------------------------------------
        err_body = json.dumps({
            "error": "not_found",
            "host": host,
            "path": path,
            "method": method,
            "case_id": case_id
        }).encode("utf-8")
        headers = {"Content-Type": "application/json; charset=utf-8"}
        self.send_exact_response(404, headers, err_body, case_id)
        self.record_transaction(method, self.path, req_body, 404, headers, err_body, case_id)

    def do_HEAD(self):
        self.handle_route("HEAD")

    def do_GET(self):
        self.handle_route("GET")

    def do_POST(self):
        self.handle_route("POST")

    def log_message(self, format, *args):
        pass

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

    http_server = HTTPServer(("0.0.0.0", HTTP_PORT), DifferentialHandler)
    print(f"[*] Differential HTTP interceptor on 0.0.0.0:{HTTP_PORT}", flush=True)

    if os.path.exists(CERT_FILE) and os.path.exists(KEY_FILE):
        https_server = HTTPServer(("0.0.0.0", HTTPS_PORT), DifferentialHandler)
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        try:
            ctx.minimum_version = ssl.TLSVersion.TLSv1
        except Exception:
            pass
        try:
            ctx.set_ciphers("ALL:@SECLEVEL=0")
        except Exception:
            pass
        ctx.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
        https_server.socket = ctx.wrap_socket(https_server.socket, server_side=True)
        print(f"[*] HTTPS server listening on 0.0.0.0:{HTTPS_PORT}", flush=True)

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
        print("[*] Differential server shut down cleanly.", flush=True)

if __name__ == "__main__":
    run()
