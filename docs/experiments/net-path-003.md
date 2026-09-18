# Experiment Report: NET-PATH-003

## Metadata
- **Identifier:** `NET-PATH-003`
- **Date:** 2026-09-17
- **Target Hardware:** Sagemcom DSI74 V2 HD GVT - BRA (STMicroelectronics STiH237)
- **Status:** **COMPLETED**
- **Outcome:** **POSITIVE (Relay verified; boot and provisioning infrastructure endpoints captured)**

---

## Executive Summary

```text
NET-PATH-003
RESULT: POSITIVE for Layer 2/3 relay verification and network infrastructure discovery.

Targeted bidirectional ARP redirection via Bettercap successfully routed the receiver's
gateway traffic through the Linux workstation. Docker forwarding policy restrictions
(-P FORWARD DROP) and ICMP redirect generation were correctly mitigated.

Observed traffic confirmed active DNS lookups to Vivo recursive resolvers (187.0.0.1)
querying Telefónica Global Video Platform STB endpoints (ucstb.vivoplay.com.br)
and outbound TCP connection attempts to legacy GVT infrastructure hosts
(186.215.183.217 and 191.32.31.251 on ports 80/443).
```

---

## Verified Topology & Network Identities

- **Observing Host (Linux PC):**
  - IP Address: `192.168.1.97/24`
  - MAC Address: `fc:aa:14:f5:c6:a2`
  - Physical Interface: `enp5s0`
- **Default Gateway (Home Router):**
  - IP Address: `192.168.1.1`
  - MAC Address: `14:ca:56:81:18:71` (ZTE Corporation)
- **Target Device (Sagemcom DSI74 V2 Receiver):**
  - MAC Address: `68:15:90:6b:81:96` (Sagemcom Broadband SAS)
  - Pre-boot IP Lease: `192.168.1.134`
  - Post-reboot IP Lease (DHCP): `192.168.1.137`

---

## Configuration & Commands Used

### 1. Kernel Routing & Redirect Mitigation
Docker was active on the host with default drop forwarding (`-P FORWARD DROP`). To allow forwarded traffic strictly for the receiver without affecting container networks or VPN interfaces, and to prevent the kernel from sending ICMP redirects telling the devices to bypass the PC:

```bash
# Suppress ICMP redirects on relay interface
sysctl -w net.ipv4.conf.all.send_redirects=0
sysctl -w net.ipv4.conf.enp5s0.send_redirects=0

# Insert targeted forwarding rules
iptables -I FORWARD 1 -i enp5s0 -o enp5s0 -s 192.168.1.134 -j ACCEPT
iptables -I FORWARD 2 -i enp5s0 -o enp5s0 -d 192.168.1.134 -j ACCEPT
# (Dynamically updated to include 192.168.1.137 upon DHCP reassignment)
iptables -I FORWARD 1 -i enp5s0 -o enp5s0 -s 192.168.1.137 -j ACCEPT
iptables -I FORWARD 2 -i enp5s0 -o enp5s0 -d 192.168.1.137 -j ACCEPT
```

### 2. Local Packet Capture
Full packet capture was initiated prior to redirection:
```bash
tcpdump -i enp5s0 -s 0 -nn -U -w captures/net-path-003.pcap \
  "host 192.168.1.134 or host 192.168.1.137 or ether host 68:15:90:6b:81:96"
```

### 3. Bidirectional ARP Redirection
Executed via Bettercap v2.41.7 with explicit interface and gateway overrides:
```bash
bettercap -iface enp5s0 -gateway-override 192.168.1.1 -silent \
  -eval "set arp.spoof.targets 192.168.1.134,192.168.1.137; set arp.spoof.fullduplex true; set arp.spoof.internal false; set arp.spoof.skip_restore false; arp.spoof on"
```

---

## Relay Verification Evidence

Hardware Ethernet address inspection confirms bidirectional interception and active forwarding:

1. **Receiver-to-Gateway Forwarding:**
   ```text
   23:51:06.536584 68:15:90:6b:81:96 > fc:aa:14:f5:c6:a2, ethertype IPv4 (0x0800): 192.168.1.134.33902 > 186.215.183.217.80: Flags [S]
   23:51:06.536692 fc:aa:14:f5:c6:a2 > 14:ca:56:81:18:71, ethertype IPv4 (0x0800): 192.168.1.134.33902 > 186.215.183.217.80: Flags [S]
   ```
   * Frame ingress: Source MAC `68:15:90:6b:81:96` (Receiver), Destination MAC `fc:aa:14:f5:c6:a2` (Workstation). Confirms receiver ARP cache poisoned to send default gateway traffic to PC.
   * Frame egress: Source MAC `fc:aa:14:f5:c6:a2` (Workstation), Destination MAC `14:ca:56:81:18:71` (Gateway). Confirms Linux kernel successfully forwarded frame out `enp5s0` towards the physical gateway.

2. **ICMP Verification:**
   * Gateway probed receiver: `192.168.1.1 > 192.168.1.134: ICMP echo request` (forwarded via PC).
   * Receiver answered gateway: `192.168.1.137 > 192.168.1.1: ICMP echo reply` (forwarded via PC).

---

## Observed Protocols & Infrastructure Endpoints

During the session and subsequent cold reboot, the receiver emitted the following network traffic:

| Timestamp (Local) | Source | Destination | Protocol / Port | Details / Resolution |
| :--- | :--- | :--- | :--- | :--- |
| `23:51:06` | `192.168.1.134:33902` | `186.215.183.217:80` | TCP [SYN] | `186.215.183.217.static.host.gvt.net.br` (SYN retries at 3s and 6s intervals; timed out) |
| `23:52:18` | `192.168.1.137:34457` | `187.0.0.1:53` | UDP / DNS | Query: `A ucstb.vivoplay.com.br.` (Resolves via CNAME to `ucstb.br.gvp.telefonica.com` $\to$ `213.140.61.225`) |
| `23:52:21` | `192.168.1.137:58875` | `191.32.31.251:443` | TCP [SYN] | `191.32.31.251.static.adsl.gvt.net.br` (HTTPS handshake attempt) |
| `23:52:25` | `192.168.1.137:60238` | `186.215.183.217:80` | TCP [SYN] | `186.215.183.217.static.host.gvt.net.br` (HTTP handshake attempt) |
| `23:52:38` | `192.168.1.137:49106` | `191.32.31.251:80` | TCP [SYN] | `191.32.31.251.static.adsl.gvt.net.br` (HTTP handshake attempt) |
| `23:53:00` | `192.168.1.137` | `192.168.1.1` | ICMP Echo Reply | Seq 1-5 responses to gateway connectivity check |

### Architectural Observations
1. **Provisioning Hostnames:** The STB firmware explicitly queries `ucstb.vivoplay.com.br` (Telefónica Global Video Platform Unified Client STB backend), pointing to Vivo Play DTH/OTT middleware.
2. **Legacy Static Host Endpoints:** The firmware contains hardcoded IP addresses or cached configuration pointing to legacy GVT subnets (`186.215.183.217` and `191.32.31.251`). These servers do not answer on ports 80/443, resulting in repeated TCP SYN timeouts.
3. **Absence of Bootloader Broadcasts:** No TFTP requests, DHCP boot options, or unsolicited UDP broadcast probes were observed during the boot loader phase prior to OS network initialization.

---

## On-Screen TV Diagnostic Correlation

Photographic captures of the receiver's on-screen user interface (`Connection Wizard` and `Connectivity • Connection Status`) directly confirm and explain the packet-level capture:

1. **Exact Firmware Build String:**
   - On-screen footer confirms: **`Versão: 1.320.1.0.5`**.
   - This provides the definitive resident firmware version tag for subsequent binary archaeology and symbol cross-referencing.

2. **Network IP Configuration Mode:**
   - The UI demonstrates `IP Settings: Manual` configured for `192.168.1.137`, mask `255.255.255.0`, gateway `192.168.1.1`, and primary/secondary DNS `187.0.0.1` / `187.0.0.2` (Vivo DNS).
   - This clarifies that `192.168.1.137` was a statically configured lease in nonvolatile flash rather than a dynamic DHCP assignment.

3. **Diagnostic Test Breakdown & Error Code:**
   - **Gateway connection: OK (Green):** Correlates exactly with the five bidirectional ICMP echo requests/replies captured at 23:52:52 – 23:53:02 via the PC forwarder.
   - **Internet connection: Error (Red):** Correlates with the TCP SYN retransmissions and timeouts to GVT hosts `186.215.183.217:80` and `191.32.31.251:80`.
   - **Establish server connection: Error (Red):** Correlates with the failure to reach `ucstb.vivoplay.com.br` (Telefónica GVP cloud backend).
   - **Vendor Diagnostic Code:** Raised **`Código 05NW`** (*"The Vivo TV interactive services are momentarily unavailable. Check the settings. If the problem persists call 106 15."*).

4. **System Clock State:**
   - The on-screen header showed `Fri, 31/12 22:05`, demonstrating that the hardware lacks a battery-backed RTC and relies on external DVB broadcast stream time (TDT/TOT) or network NTP sync, neither of which succeeded.

---

## Cleanup & State Restoration Confirmation

All temporary modifications have been fully reverted:
- **ARP Redirection:** Terminated; Bettercap sent unsolicited ARP replies restoring legitimate MAC addresses for `192.168.1.1`, `192.168.1.134`, and `192.168.1.137`.
- **Firewall Rules:** Temporary `FORWARD` ACCEPT rules were deleted. `iptables -S FORWARD` restored to baseline:
  ```text
  -P FORWARD DROP
  -A FORWARD -j ts-forward
  -A FORWARD -j DOCKER-USER
  -A FORWARD -j DOCKER-FORWARD
  ```
- **Kernel Redirects:** Restored to defaults:
  - `net.ipv4.conf.all.send_redirects = 1`
  - `net.ipv4.conf.enp5s0.send_redirects = 1`
- **Docker & Workstation Connectivity:** Preserved `net.ipv4.ip_forward = 1`; verified gateway ping round-trip ($0.5\text{ ms}$) and receiver reachability ($2.1\text{ ms}$).

---

## Next Justified Action

The network diagnostic confirmed that the stock firmware relies on remote cloud endpoints (`ucstb.vivoplay.com.br` and legacy GVT IPs) that are largely unreachable or decommissioned, with no local listening ports or network recovery boot loaders.

**Justified Action:** Proceed with **BOOT-CHAIN-001** (hardware-level analysis: locating the UART test pads and reading SPI NOR flash directly via external programmer). Firmware reverse engineering from dumped SPI flash is required to locate the update URL schema, public keys, and boot environment parameters.
