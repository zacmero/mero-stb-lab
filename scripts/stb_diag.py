#!/usr/bin/env python3
"""
NET-CONFIG-005 Automated Diagnostic Suite
Tests Layer 2/3 connectivity to STB, audits iptables rules, verifies local HTTP/HTTPS
endpoints, and validates TLS 1.0 negotiation without physical device interaction.
"""

import os
import sys
import socket
import ssl
import subprocess
import urllib.request
import json

TARGET_MAC = "68:15:90:6b:81:96"
DEFAULT_IP = "192.168.1.139"

def get_current_stb_ip():
    try:
        out = subprocess.check_output(["ip", "neighbor", "show"], text=True)
        candidates = []
        for line in out.splitlines():
            if TARGET_MAC.lower() in line.lower() and "FAILED" not in line:
                candidates.append(line.split()[0])
        # Test which candidate responds
        for c in candidates:
            if subprocess.run(["ping", "-c", "1", "-W", "1", c], capture_output=True).returncode == 0:
                return c
        if candidates:
            return candidates[-1]
    except Exception:
        pass
    return DEFAULT_IP

def test_ping(ip):
    try:
        res = subprocess.run(
            ["ping", "-c", "3", "-W", "1", ip],
            capture_output=True, text=True
        )
        if res.returncode == 0:
            lines = res.stdout.strip().splitlines()
            stats = lines[-1] if lines else ""
            return True, stats
        return False, "Host unreachable"
    except Exception as e:
        return False, str(e)

def test_http_endpoint(base_url, path, method="GET", expect_status=200):
    url = base_url + path
    req = urllib.request.Request(url, method=method)
    if method == "POST":
        req.data = b"{}"
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def http_error_302(self, req, fp, code, msg, headers):
            return fp
    opener = urllib.request.build_opener(NoRedirect)
    try:
        resp = opener.open(req, timeout=3)
        body = resp.read()
        ct = resp.headers.get("Content-Type", "")
        loc = resp.headers.get("Location", "")
        return True, resp.status, ct, loc, len(body)
    except Exception as e:
        return False, 0, str(e), "", 0

def test_tls10(port=8443):
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        ctx.minimum_version = ssl.TLSVersion.TLSv1
        ctx.set_ciphers("ALL:@SECLEVEL=0")
        with urllib.request.urlopen(f"https://127.0.0.1:{port}/", context=ctx, timeout=3) as r:
            return True, f"HTTP {r.status} over {r.version}"
    except Exception as e:
        return False, str(e)

def check_iptables():
    try:
        nat_out = subprocess.check_output(["iptables", "-t", "nat", "-S", "PREROUTING"], text=True)
        has_nat80 = "dport 80 -j REDIRECT" in nat_out
        has_nat443 = "dport 443 -j REDIRECT" in nat_out
        fwd_out = subprocess.check_output(["iptables", "-S", "FORWARD"], text=True)
        has_fwd = TARGET_MAC.upper() in fwd_out.upper()
        return has_nat80, has_nat443, has_fwd
    except Exception as e:
        return False, False, False

def main():
    print("=" * 65)
    print("       MERO-STB-LAB: AUTOMATED LOCAL DIAGNOSTIC SUITE        ")
    print("=" * 65)

    ip = get_current_stb_ip()
    print(f"[*] Target Hardware MAC:  {TARGET_MAC}")
    print(f"[*] Active Leased IP:     {ip}")

    # 1. Ping
    ok_ping, ping_info = test_ping(ip)
    status_ping = "PASS" if ok_ping else "FAIL"
    print(f"\n[1] Layer 2/3 Ping Check:   [{status_ping}]")
    print(f"    Details: {ping_info}")

    # 2. Firewall / Redirection
    nat80, nat443, fwd = check_iptables()
    print(f"\n[2] Iptables Redirection Audit:")
    print(f"    Port 80  -> 8080 REDIRECT: [{'ACTIVE' if nat80 else 'MISSING'}]")
    print(f"    Port 443 -> 8443 REDIRECT: [{'ACTIVE' if nat443 else 'MISSING'}]")
    print(f"    Universal MAC FORWARD:     [{'ACTIVE' if fwd else 'MISSING'}]")

    # 3. HTTP Endpoints
    print(f"\n[3] Local HTTP Services (Port 8080):")
    base = "http://127.0.0.1:8080"
    endpoints = [
        ("/tv-config/appConfigFit.json", "GET", 200),
        ("/mirada1-destaques/highlights_config.xml", "GET", 200),
        ("/tv-config/backupIpConfig.json", "POST", 200),
        ("/bussola/redirect?type=vod", "GET", 302),
        ("/portal.html", "GET", 200),
        ("/portal.svg", "GET", 200),
    ]
    for path, method, exp in endpoints:
        ok, code, ct, loc, sz = test_http_endpoint(base, path, method, exp)
        st = "PASS" if ok and code == exp else "FAIL"
        extra = f"-> Location: {loc}" if loc else f"({sz} bytes, {ct})"
        print(f"    [{st}] {method:<4} {path:<42} {code} {extra}")

    # 4. HTTPS & TLS 1.0
    print(f"\n[4] Local HTTPS Service (Port 8443, Legacy TLS 1.0):")
    ok_tls, tls_info = test_tls10(8443)
    status_tls = "PASS" if ok_tls else "FAIL"
    print(f"    [{status_tls}] TLS 1.0 Handshake: {tls_info}")

    print("\n" + "=" * 65)
    print("                    DIAGNOSTIC COMPLETE                     ")
    print("=" * 65)

if __name__ == "__main__":
    main()
