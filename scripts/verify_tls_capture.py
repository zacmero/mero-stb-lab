#!/usr/bin/env python3
"""
Recover and verify TLS evidence from PCAP without hardcoded conclusions.
"""
import sys
import os
import struct

def parse_pcap_tls(pcap_path):
    if not os.path.exists(pcap_path):
        return {"status": "FILE_NOT_FOUND", "records": []}

    with open(pcap_path, "rb") as f:
        data = f.read()

    offset = 24
    records = []
    while offset < len(data):
        ts_sec, ts_usec, incl_len, orig_len = struct.unpack("<IIII", data[offset:offset+16])
        pkt = data[offset+16:offset+16+incl_len]
        offset += 16 + incl_len
        if len(pkt) < 34: continue
        if pkt[12:14] != b"\x08\x00": continue # IPv4
        if pkt[23] != 6: continue # TCP
        src_ip = ".".join(str(b) for b in pkt[26:30])
        dst_ip = ".".join(str(b) for b in pkt[30:34])
        ip_hdr_len = (pkt[14] & 0x0f) * 4
        tcp_hdr = pkt[14+ip_hdr_len:]
        if len(tcp_hdr) < 20: continue
        sp, dp = struct.unpack("!HH", tcp_hdr[:4])
        data_off = ((tcp_hdr[12] >> 4) & 0x0f) * 4
        payload = tcp_hdr[data_off:]
        if (sp in (443, 8443) or dp in (443, 8443)) and len(payload) >= 5:
            content_type = payload[0]
            version = struct.unpack("!H", payload[1:3])[0]
            length = struct.unpack("!H", payload[3:5])[0]
            
            # Sub-parse Handshake or Alert
            detail = ""
            if content_type == 22 and len(payload) >= 6: # Handshake
                htype = payload[5]
                htypes = {1: "ClientHello", 2: "ServerHello", 11: "Certificate", 12: "ServerKeyExchange", 14: "ServerHelloDone"}
                detail = htypes.get(htype, f"Handshake({htype})")
                if htype == 1 and len(payload) >= 11:
                    c_ver = struct.unpack("!H", payload[9:11])[0]
                    detail += f" (client_version={hex(c_ver)})"
            elif content_type == 21 and len(payload) >= 7: # Alert
                level = payload[5]
                desc = payload[6]
                levels = {1: "warning", 2: "fatal"}
                alerts = {0: "close_notify", 10: "unexpected_message", 20: "bad_record_mac",
                          40: "handshake_failure", 42: "bad_certificate", 43: "unsupported_certificate",
                          44: "certificate_revoked", 45: "certificate_expired", 46: "certificate_unknown",
                          47: "illegal_parameter", 48: "unknown_ca", 70: "protocol_version"}
                detail = f"Alert level={levels.get(level, level)} desc={alerts.get(desc, desc)} ({desc})"

            records.append({
                "timestamp": f"{ts_sec}.{ts_usec:06d}",
                "src": f"{src_ip}:{sp}",
                "dst": f"{dst_ip}:{dp}",
                "content_type": content_type,
                "version": hex(version),
                "length": length,
                "detail": detail,
                "raw_hex": payload[:min(len(payload), 32)].hex()
            })

    return {"status": "OK", "count": len(records), "records": records}

if __name__ == "__main__":
    pcap = sys.argv[1] if len(sys.argv) > 1 else "/home/zacmero/projects/mero-stb-lab/captures/net-config-005.pcap"
    res = parse_pcap_tls(pcap)
    print(f"Status: {res['status']}, Found: {res.get('count', 0)} TLS records")
    for r in res.get("records", []):
        t_name = {20: "ChangeCipherSpec", 21: "Alert", 22: "Handshake", 23: "ApplicationData"}.get(r["content_type"], str(r["content_type"]))
        print(f"[{r['timestamp']}] {r['src']} -> {r['dst']} | {t_name:<16} | {r['version']} | {r['detail']}")
