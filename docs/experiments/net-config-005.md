# Experiment Report: NET-CONFIG-005

## Metadata
- **Identifier:** `NET-CONFIG-005`
- **Date:** 2026-09-18
- **Target Hardware:** Sagemcom DSI74 V2 HD GVT (STMicroelectronics STiH237)
- **Status:** **COMPLETED (Phase 1 Differential Run)**
- **Outcome:** **NO NEW CAPABILITY DEMONSTRATED**
- **Operating Constraint:** $0 Budget / Software & Ethernet Only

---

## 1. Executive Summary

```text
NET-CONFIG-005: Differential Endpoint & Navigation Campaign
RESULT: NO NEW CAPABILITY DEMONSTRATED.

1. HARNESS AUDIT & ISOLATION:
   The HTTP/HTTPS interceptor was completely overhauled to enforce exact
   Host + Method + Path routing, bounded body reads (64KB max, 2.0s timeout),
   and SHA-256 body hashing. Transactions are segregated by hardware source:
   RECEIVER_HW (MAC 68:15:90:6b:81:96) is strictly separated from LOCAL_SELFTEST.

2. TLS HARDWARE CONSTRAINTS:
   Analysis of raw PCAP frames confirms the receiver rejects self-signed certificates
   with TLS Alert 48 (unknown_ca). Hardcoded operator CA certificates in firmware
   prevent HTTPS MITM without certificate store extraction.

3. DISSECTION OF HISTORICAL "REDIRECTION":
   Inspection of prior sessions revealed that requests for `/portal.svg` were
   driven by an HTTP 302 Found response (`Location: /portal.svg`), NOT by client
   parsing of JSON navigation keys. The client XHR sent `Accept: application/json`,
   received raw SVG, failed JSON parsing, and rendered a connection error.

4. DIFFERENTIAL TEST CAMPAIGN:
   An automated 12-case differential battery was deployed against `/bussola/redirect`
   and `/tv-config/appConfigFit.json`. In passive autonomous execution without
   remote-control trigger events, all 12 cases remained UNTESTED.
```

---

## 2. Differential Campaign Battery & Results

The campaign tests single candidate properties in HTTP 200 JSON responses without `Location` headers, comparing them against a repeatable baseline (`{"status":"ok","code":0}`).

| Case ID | Target Endpoint | Provenance | Candidate Property Tested | Expected Marker | Actual Result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **CASE-00-BASELINE** | `/bussola/redirect` | Control baseline | None (`{"status":"ok","code":0}`) | None | `UNTESTED` |
| **CASE-01-BUSSOLA-URL** | `/bussola/redirect` | Guess (REST convention) | `{"url": "/marker/bussola_c01_url"}` | `/marker/bussola_c01_url` | `UNTESTED` |
| **CASE-02-BUSSOLA-PORTALURL** | `/bussola/redirect` | Ekioh ecosystem artifact | `{"portalUrl": "/marker/bussola_c02_portalurl"}` | `/marker/bussola_c02_portalurl` | `UNTESTED` |
| **CASE-03-BUSSOLA-REDIRECTURL** | `/bussola/redirect` | Guess (Mirada camelCase) | `{"redirectUrl": "/marker/bussola_c03_redirecturl"}` | `/marker/bussola_c03_redirecturl` | `UNTESTED` |
| **CASE-04-BUSSOLA-TARGET** | `/bussola/redirect` | Guess (SVG/DOM target) | `{"target": "/marker/bussola_c04_target"}` | `/marker/bussola_c04_target` | `UNTESTED` |
| **CASE-05-BUSSOLA-RESULT-URL** | `/bussola/redirect` | Mirada schema reference | `{"result": {"url": "/marker/bussola_c05_resulturl"}}` | `/marker/bussola_c05_resulturl` | `UNTESTED` |
| **CASE-06-BUSSOLA-DATA-URL** | `/bussola/redirect` | Guess (JSON-RPC wrapper) | `{"data": {"url": "/marker/bussola_c06_dataurl"}}` | `/marker/bussola_c06_dataurl` | `UNTESTED` |
| **CASE-07-BUSSOLA-ACTION-OPEN** | `/bussola/redirect` | Mirada middleware spec | `{"action": "open", "url": "/marker/bussola_c07_action"}` | `/marker/bussola_c07_action` | `UNTESTED` |
| **CASE-08-BUSSOLA-VODURL** | `/bussola/redirect` | Query parameter (`type=vod`) | `{"vodUrl": "/marker/bussola_c08_vodurl"}` | `/marker/bussola_c08_vodurl` | `UNTESTED` |
| **CASE-09-BUSSOLA-ISOLATED-302** | `/bussola/redirect` | HTTP standard redirect | HTTP 302 + `Location: /marker/bussola_c09_302` | `/marker/bussola_c09_302` | `UNTESTED` |
| **CASE-10-APPCONFIG-PORTALURL** | `/tv-config/appConfigFit.json` | Sagemcom config artifact | `{"portalUrl": "/marker/cfg_c10_portalurl"}` | `/marker/cfg_c10_portalurl` | `UNTESTED` |
| **CASE-11-APPCONFIG-STARTURL** | `/tv-config/appConfigFit.json` | Sagemcom firmware string | `{"startUrl": "/marker/cfg_c11_starturl"}` | `/marker/cfg_c11_starturl` | `UNTESTED` |

*Note: Per testing protocol, cases where the receiver made zero requests during the evaluation window are strictly classified as `UNTESTED`, not negative.*

---

## 3. Empirical Findings & Technical Evidence

### 3.1 Receiver Network Profile
- **MAC Address:** `68:15:90:6b:81:96` (Sagemcom Broadband SAS)
- **Active DHCP Lease:** `192.168.1.146` on `enp5s0`
- **ICMP Latency:** 0.91 ms min / 2.78 ms avg / 0% packet loss
- **Path MTU:** 1500 bytes unfragmented
- **Inbound Attack Surface:** All 50 probed TCP ports filtered/dropped. Device does not run unsolicited listening services on the LAN interface.

### 3.2 TLS Cryptographic Enforcement
- Extraction of TLS alert records from `captures/net-config-005.pcap` demonstrates hardware rejection:
  ```text
  Frame Timestamp: 1789708881.384119
  Source: 192.168.1.139:46382 -> Destination: 191.32.31.251:8443
  Type: Alert (21)
  Level: Fatal (2)
  Description: Unknown CA (48)
  ```
- **Conclusion:** Hardware root store is immutable over network without physical flash read.

### 3.3 Root Cause of Previous "Connection Error"
Captured XHR headers demonstrate that when entering interactive VOD ("Vivo Play"), the browser issues an asynchronous XMLHttpRequest expecting JSON:
```http
GET /bussola/redirect?type=vod&user=035289282213&product=DSI74%20V2%20HD%20GVT&fw=RC1.12.12&sw=1.0.5 HTTP/1.1
User-Agent: Ekioh v2.2.4.5-sagem (Mar  2 2013) r10767
Host: 191.32.31.251
Connection: Keep-Alive
Accept: application/json, text/plain, */*
```
When the server responded with an HTTP 302 pointing to `/portal.svg`, the client followed the redirect and received SVG XML markup. The internal JavaScript routine attempted `JSON.parse()` on the markup, raised a SyntaxError, caught the exception, and displayed the error banner.

---

## 4. Evidence Classification

| Milestone Level | Demonstrated? | Evidence Backing |
| :--- | :--- | :--- |
| **Response Delivered** | **YES** (Prior sessions) | `net-config-005.log` records HTTP 200 and 302 responses sent to receiver |
| **Changed Application Behavior** | **YES** (Visual banner) | Receiver displays connection error on invalid JSON, XML text on highlights |
| **Marker URL Fetched (via JSON field)** | **NO** | 0 receiver requests to `/marker/*` without HTTP 302 header |
| **Marker URL Fetched (via HTTP 302)** | **YES** (Prior sessions) | Client followed 302 to `/portal.svg` via libcurl / XHR redirect |
| **Document Visibly Rendered** | **NO** | Raw SVG/HTML never rendered in top-level viewport |
| **Supplied JavaScript Executed** | **NO** | 0 callbacks received on `/report/script_exec` |
| **Native / System Capability** | **NO** | 0 execution vectors exposed |

---

## 5. Smallest Reproducible Positive Case Found

**None.** At this stage, no JSON navigation field has demonstrably triggered an outbound HTTP fetch from the receiver.

---

## 6. Single Justified Next Experiment

**Manual Single-Case Differential Trigger via Remote Control:**
Because the receiver only queries `/bussola/redirect` when the user actively presses "Vivo Play" or "Menu", autonomous passive waiting yields `UNTESTED`.
The single justified next experiment is to lock the harness to **CASE-01-BUSSOLA-URL**, prompt the user for **one** press of "Vivo Play", and monitor `experiment_transactions.jsonl` for a 30-second window. If negative, advance one-by-one to CASE-02 through CASE-08 with a single button press per test.


---

## 7. Safety Incident / Harness Correction (2026-09-18)

After the Phase 1 campaign, the original harness caused a temporary LAN outage.

### Root cause
`run_net_config_005.sh` supplied the ARP redirector with every address from
`192.168.1.128` through `192.168.1.160`. During cleanup, the old
`arp_spoofer.py` then emitted restoration frames that asserted each of those
addresses belonged to the single Sagemcom STB MAC (`68:15:90:6b:81:96`).

That meant unrelated DHCP clients inside the range could be incorrectly associated
with the STB MAC in the gateway's ARP cache, breaking return traffic to those clients.

### Recovery observed
Disconnecting the STB/host from the LAN and power-cycling the router immediately
restored connectivity, consistent with volatile ARP-cache corruption rather than a
persistent router configuration change.

### Mandatory correction
The unsafe range-based design is retired. Future runs must:
- resolve exactly one live STB IP from the known STB MAC;
- abort on zero or multiple candidate IPs;
- poison only STB <-> gateway;
- restore only the authentic STB/gateway bindings;
- require explicit human arming;
- verify gateway reachability after cleanup.

See `AGENTS.md` and the hardened `scripts/arp_spoofer.py` /
`scripts/run_net_config_005.sh` before any further live test.
