# NETWORK-SERVICE-011: Exact-Device Service Inventory

**Date:** 2026-09-19  
**Target:** `192.168.1.57` / `68:15:90:6b:81:96`  
**Result:** **COMPLETED — NO LAN-REACHABLE SERVICE IDENTIFIED**

## Objective

Determine whether the receiver exposes a legitimate shell, maintenance interface, RPC endpoint, discovery service, or other LAN-facing path to the operating system without launching the injected Ekioh application.

## Safety and scope

The host populated its neighbor entry with one targeted ICMP probe and verified that `192.168.1.57` resolved to the exact receiver MAC before scanning. No ARP interception, firewall mutation, sysctl mutation, or Vivo Play launch occurred.

The full TCP sweep was rate-limited to 300–500 SYN packets per second with one retry. UDP work used a top-200 sweep followed by protocol-aware probes against 17 STB-relevant ports. A final 60-second capture was passive.

## Results

### TCP

All 65,535 TCP ports returned no response and were classified `filtered` by Nmap. No TCP banner, shell, web server, SSH, Telnet, RPC, or maintenance listener was reachable from this LAN host.

Artifact prefix: `captures/network-service-011-tcp-discovery`

### UDP

The top 200 UDP ports returned no response and were classified `open|filtered`. This classification is ambiguous and does not prove that any UDP port is open.

Protocol-aware probes covered:

```text
53, 67, 68, 69, 123, 137, 138, 161, 162,
500, 514, 520, 623, 1900, 4500, 5353, 5683
```

DNS service discovery, NTP, SNMP, SSDP/UPnP, and TFTP scripts received no application response. The bounded targeted run ended at its five-minute host timeout without identifying a service.

Artifact prefixes:

- `captures/network-service-011-udp-top200`
- `captures/network-service-011-udp-targeted`

### Passive observation

A 60-second Ethernet capture filtered to the receiver MAC recorded zero packets while the receiver was idle. This interval did not include a boot, remote action, or scheduled service transaction and therefore establishes only that no broadcast/multicast activity occurred during that window.

Artifact: `captures/network-service-011-passive.pcap`

## Interpretation

The receiver silently filters unsolicited LAN traffic. This blocks a direct inbound terminal path from the tested host but does not establish that the OS has no listening services internally or on other interfaces. Outbound receiver-initiated HTTP traffic remains the demonstrated network entry path.

The next network work should focus on receiver-initiated protocols, captured firmware/update artifacts, and exact application callbacks rather than broader inbound scanning.

## Evidence boundary

Concrete tests for the remaining service classes are documented in `app-api-009b-media-010.md`: pre-power boot-window capture with narrow timed exact-target probes; observation and exact emulation of receiver-initiated flows; and firmware, console, or native-footprint analysis for loopback-only services. The last class cannot be established or excluded by more remote LAN scanning.

NETWORK-SERVICE-011 does not prove that all UDP ports are closed, that no loopback/internal service exists, or that firmware contains no maintenance daemon. It proves only that the tested LAN host received no service response under the documented probes.
