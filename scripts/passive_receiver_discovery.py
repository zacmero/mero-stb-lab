#!/usr/bin/env python3
"""
MERO-STB-LAB: Passive Receiver Broadcast Discovery
Listens on the specified interface for DHCP and ARP broadcast frames carrying
the exact target MAC address. Does NOT transmit any packets on the network.
"""

import sys
import time
import socket
import struct

def mac_str_to_bytes(s):
    clean = s.replace(":", "").replace("-", "").strip().lower()
    return bytes.fromhex(clean)

def discover_receiver_ip(iface, target_mac_str, timeout=120):
    target_mac = mac_str_to_bytes(target_mac_str)
    discovered_ips = set()

    try:
        sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(0x0003))
        sock.bind((iface, 0))
        sock.settimeout(1.0)
    except Exception as e:
        print(f"[-] Failed to open raw packet socket on {iface}: {e}", file=sys.stderr, flush=True)
        return []

    print(f"[*] Passively capturing DHCP/ARP broadcast frames on {iface} for MAC {target_mac_str}...", file=sys.stderr, flush=True)
    print(f"[*] ACTION: Reboot / power-cycle the receiver now while capture is active (listening up to {timeout}s)...", file=sys.stderr, flush=True)

    start_time = time.time()
    last_print = 0

    while time.time() - start_time < timeout:
        elapsed = int(time.time() - start_time)
        if elapsed % 15 == 0 and elapsed != last_print:
            last_print = elapsed
            print(f"[*] Listening... ({elapsed}/{timeout}s elapsed, {len(discovered_ips)} candidate IP(s) found)", file=sys.stderr, flush=True)

        try:
            pkt, addr = sock.recvfrom(2048)
        except socket.timeout:
            continue
        except Exception as e:
            print(f"[-] Socket read error: {e}", file=sys.stderr, flush=True)
            break

        if len(pkt) < 14:
            continue

        eth_src = pkt[6:12]
        eth_type = struct.unpack("!H", pkt[12:14])[0]

        # 1. Inspect ARP (EtherType 0x0806)
        if eth_type == 0x0806 and len(pkt) >= 42:
            arp = pkt[14:42]
            hw_type, proto_type, hw_len, proto_len, opcode = struct.unpack("!HHBBH", arp[:8])
            if hw_type == 1 and proto_type == 0x0800 and hw_len == 6 and proto_len == 4:
                sender_mac = arp[8:14]
                sender_ip = arp[14:18]
                if sender_mac == target_mac:
                    ip_str = socket.inet_ntoa(sender_ip)
                    if ip_str != "0.0.0.0":
                        discovered_ips.add(ip_str)
                        print(f"[+] Broadcast ARP observed from {target_mac_str}: Sender IP = {ip_str}", file=sys.stderr, flush=True)

        # 2. Inspect IPv4 (EtherType 0x0800) for DHCP (UDP 67 / 68)
        elif eth_type == 0x0800 and len(pkt) >= 34:
            ip_hdr = pkt[14:]
            ver_ihl = ip_hdr[0]
            ihl = (ver_ihl & 0x0f) * 4
            if len(ip_hdr) >= ihl + 8:
                proto = ip_hdr[9]
                if proto == 17:  # UDP
                    udp_hdr = ip_hdr[ihl:ihl+8]
                    src_port, dst_port, udp_len = struct.unpack("!HHH", udp_hdr[:6])
                    if (src_port in (67, 68) or dst_port in (67, 68)) and len(ip_hdr) >= ihl + 8 + 240:
                        bootp = ip_hdr[ihl+8:]
                        op = bootp[0]
                        ciaddr = socket.inet_ntoa(bootp[12:16])
                        yiaddr = socket.inet_ntoa(bootp[16:20])
                        chaddr = bootp[28:34]  # client hardware address

                        if chaddr == target_mac:
                            if op == 2 and yiaddr != "0.0.0.0":
                                discovered_ips.add(yiaddr)
                                print(f"[+] Broadcast DHCP ACK/Reply for {target_mac_str}: Your-IP = {yiaddr}", file=sys.stderr, flush=True)
                            elif op == 1:
                                if ciaddr != "0.0.0.0":
                                    discovered_ips.add(ciaddr)
                                    print(f"[+] Broadcast DHCP Request from {target_mac_str}: Client-IP = {ciaddr}", file=sys.stderr, flush=True)
                                # Parse DHCP options for Option 50 (Requested IP)
                                if len(bootp) > 240 and bootp[236:240] == b"\x63\x82\x53\x63":
                                    opt_idx = 240
                                    while opt_idx < len(bootp):
                                        opt_code = bootp[opt_idx]
                                        if opt_code == 255:
                                            break
                                        if opt_code == 0:
                                            opt_idx += 1
                                            continue
                                        if opt_idx + 1 >= len(bootp):
                                            break
                                        opt_len = bootp[opt_idx + 1]
                                        opt_data = bootp[opt_idx+2:opt_idx+2+opt_len]
                                        if opt_code == 50 and opt_len == 4:
                                            req_ip = socket.inet_ntoa(opt_data)
                                            discovered_ips.add(req_ip)
                                            print(f"[+] Broadcast DHCP Request from {target_mac_str}: Requested-IP = {req_ip}", file=sys.stderr, flush=True)
                                        opt_idx += 2 + opt_len

        # If exactly one candidate discovered and seen stably, break early after 3s grace
        if len(discovered_ips) == 1 and (time.time() - start_time > 4):
            break

    sock.close()
    return sorted(discovered_ips)

if __name__ == "__main__":
    iface_arg = sys.argv[1] if len(sys.argv) > 1 else "enp5s0"
    target_mac_arg = sys.argv[2] if len(sys.argv) > 2 else "68:15:90:6b:81:96"
    timeout_arg = int(sys.argv[3]) if len(sys.argv) > 3 else 120

    candidates = discover_receiver_ip(iface_arg, target_mac_arg, timeout_arg)
    for c in candidates:
        print(c)
