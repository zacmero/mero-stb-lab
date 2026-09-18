# Plan & Tracking: NET-PROVISION-004

## Metadata
- **Identifier:** `NET-PROVISION-004`
- **Date:** 2026-09-18
- **Target:** Sagemcom DSI74 V2 HD GVT (STiH237)
- **Status:** **IN PROGRESS**
- **Operating Constraint:** $0 Budget / Software & Network Only

---

## Objective

Intercept and capture the unencrypted HTTP requests transmitted by the receiver to legacy GVT infrastructure IP addresses (`186.215.183.217:80` and `191.32.31.251:80`) during boot and network diagnostics, identify requested resources (URIs, query tokens, device headers), and evaluate potential for network-delivered configuration or firmware injection.

---

## Technical Architecture

```text
[ Sagemcom DSI74 V2 ]
  IP: 192.168.1.137
  Sends HTTP GET to: 186.215.183.217:80 / 191.32.31.251:80
         │
         │ (Ethernet via PC Relay)
         ▼
[ Linux Host (enp5s0: 192.168.1.97) ]
  1. iptables PREROUTING (nat):
     Redirect dport 80 destined to 186.215.183.217 / 191.32.31.251 -> 192.168.1.97:8080
  2. Local Python HTTP Logger:
     Listens on 0.0.0.0:8080, completes TCP handshake, logs full request headers and body.
  3. Response Strategy:
     - Phase A: Return HTTP 200 OK with empty body / inspection banner.
     - Phase B: Return structured mock response based on observed URI pattern.
```

---

## Task Checklist

- [x] **Task 1: Requirements & Constraints Definition**
  - Lock $0 budget constraint; establish software-only network emulation path.
- [x] **Task 2: Create Persistent Roadmap & Tracking Files**
  - Document all three zero-cost exploration vectors in [`ROADMAP.md`](../../ROADMAP.md).
  - Initialize [`docs/experiments/plan-net-provision-004.md`](plan-net-provision-004.md).
- [x] **Task 3: Develop Lightweight HTTP Interceptor Script**
  - Implement standalone Python script (`scripts/http_interceptor.py`) logging timestamp, method, path, headers, and body.
- [x] **Task 4: Build Integrated Session Runner with Safe Teardown**
  - Script (`scripts/run_net_provision_004.sh`) managing:
    - ICMP redirect suppression (`send_redirects=0`)
    - Forwarding rules for `192.168.1.137`
    - PREROUTING DNAT / REDIRECT rules for port 80 targets
    - Background Bettercap ARP redirection
    - Trapped cleanup restoring all firewall and kernel parameters on exit.
- [x] **Task 5: Execute Test & Trigger Diagnostic on TV**
  - Launch runner session.
  - User triggers "Testar Conexão" from TV menu and reboots receiver.
  - Intercepted port 80 traffic, completed TCP handshake, and captured raw HTTP request.
- [x] **Task 6: Analyze Request Payloads & Compile Findings**
  - Extracted User-Agent: `Ekioh v2.2.4.5-sagem (Mar  2 2013) r10767`.
  - Identified target endpoint: `GET /tv-config/appConfigFit.json HTTP/1.1`.
  - Verified receiver ACK and parsing of mock JSON response.
  - Documented complete findings in [`net-provision-004.md`](net-provision-004.md).

---

## Log of Findings & Observations

### Observation 1: Menu Diagnostic Scope (Local Time: 00:43:44 - 00:43:49)
- Two consecutive on-screen "Test Connection" executions were captured in `captures/net-provision-004.pcap`.
- **Observed Traffic:** Exclusively 5 bidirectional ICMP echo requests and replies between gateway `192.168.1.1` and receiver `192.168.1.137` per test run.
- **Deduction:** The UI "Test Connection" wizard checks only local gateway ICMP reachability. It does not spawn background HTTP/DNS queries on demand.
- **Implication:** The unencrypted HTTP queries to `186.215.183.217:80` and `191.32.31.251:80` and DNS lookups for `ucstb.vivoplay.com.br` are triggered during **system initialization at cold-boot** or upon launching interactive middleware (e.g. Vivo Play / Portal).
- **Next Step:** Perform a receiver reboot (or launch Vivo Play/Portal from remote) while the interceptor session is actively running to capture the boot HTTP requests into port 8080.
