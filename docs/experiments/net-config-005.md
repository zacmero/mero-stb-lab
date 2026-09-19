# Experiment Report: NET-CONFIG-005

## Metadata
- **Identifier:** `NET-CONFIG-005`
- **Date:** 2026-09-18
- **Target Hardware:** Sagemcom DSI74 V2 HD GVT (STMicroelectronics STiH237)
- **Status:** **COMPLETED (Interactive Three-Case Protocol)**
- **Outcome:** **NO NEW CAPABILITY DEMONSTRATED**
- **Operating Constraint:** $0 Budget / Software & Ethernet Only

---

## 1. Executive Summary

```text
NET-CONFIG-005: Interactive Three-Case Protocol
RESULT: NO NEW CAPABILITY DEMONSTRATED.

1. EXACT-TARGET ISOLATION:
   The harness enforces strict single-target ARP redirection between the verified
   receiver (192.168.1.54, 68:15:90:6b:81:96) and gateway (192.168.1.1, 14:ca:56:81:18:71).
   All preflight and post-interception health checks on gateway, DNS, and HTTPS
   passed with zero disruption to host networking.

2. CASE-00-BASELINE:
   Delivered HTTP 200 JSON minimal payload {"status":"ok","code":0} to RECEIVER_HW.
   Confirmed with matching case_id, run_id, and response SHA-256. Observed for 30.0s.
   Verdict: DELIVERED.

3. CASE-09-BUSSOLA-ISOLATED-302:
   Delivered HTTP 302 Found with Location: http://191.32.31.251/marker/bussola_c09_302.
   Matched case_id, run_id, and response SHA-256. During the 30.0s observation window,
   the receiver did NOT follow the redirect to /marker/bussola_c09_302.
   Verdict: NEGATIVE. Classified strictly as HTTP redirect behavior, not JSON navigation.

4. CASE-01-BUSSOLA-URL:
   Delivered HTTP 200 JSON candidate {"status":"ok","code":0,"url":"http://191.32.31.251/marker/bussola_c01_url"}
   with strictly no Location header. Matched case_id, run_id, and response SHA-256.
   During the 30.0s observation window, the receiver did NOT fetch /marker/bussola_c01_url.
   Verdict: NEGATIVE.
```

---

## 2. Interactive Three-Case Results Table

| Case ID | Target Endpoint | Candidate Property Tested | Response Status & Headers | Expected Marker | Marker Hit | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **CASE-00-BASELINE** | `/bussola/redirect` | Baseline (`{"status":"ok","code":0}`) | HTTP 200 (`application/json`) | None | False | **DELIVERED** |
| **CASE-09-BUSSOLA-ISOLATED-302** | `/bussola/redirect` | HTTP 302 Redirect Baseline | HTTP 302 (`Location: .../bussola_c09_302`) | `/marker/bussola_c09_302` | False | **NEGATIVE** |
| **CASE-01-BUSSOLA-URL** | `/bussola/redirect` | `{"url": ".../bussola_c01_url"}` | HTTP 200 (No Location header) | `/marker/bussola_c01_url` | False | **NEGATIVE** |

---

## 3. Verified Hardware Transactions (from `captures/differential_results.json`)

### Transaction 1: CASE-00-BASELINE
- **Timestamp:** `2026-09-19T00:00:23.701541Z`
- **Client:** `192.168.1.54:51318` (`RECEIVER_HW`)
- **Request:** `GET /bussola/redirect?type=vod&user=035289282213&product=DSI74%20V2%20HD%20GVT&fw=RC1.12.12&sw=1.0.5 HTTP/1.1`
- **Host:** `191.32.31.251`
- **Case ID / Run ID:** `CASE-00-BASELINE` / `CASE-00-BASELINE-1789775953784902300`
- **Delivered Status:** `HTTP 200 OK` (27 bytes)
- **Response SHA-256:** `34ac3bd2dc2dece014471a2cd4a99cab0cc90dc97c856a69c5008b1f482d82ce`
- **Observation:** Full 30.0s elapsed.

### Transaction 2: CASE-09-BUSSOLA-ISOLATED-302
- **Timestamp:** `2026-09-19T00:02:13.157205Z`
- **Client:** `192.168.1.54:51321` (`RECEIVER_HW`)
- **Request:** `GET /bussola/redirect?type=vod&user=035289282213&product=DSI74%20V2%20HD%20GVT&fw=RC1.12.12&sw=1.0.5 HTTP/1.1`
- **Host:** `191.32.31.251`
- **Case ID / Run ID:** `CASE-09-BUSSOLA-ISOLATED-302` / `CASE-09-BUSSOLA-ISOLATED-302-1789776075779905379`
- **Delivered Status:** `HTTP 302 Found` (22 bytes, Location: `http://191.32.31.251/marker/bussola_c09_302`)
- **Response SHA-256:** `1d5b09e807c8c9b7e8c620110533ee77483729c9ac1107898aeda548ef95540e`
- **Observation:** Full 30.0s elapsed. Marker `/marker/bussola_c09_302` was not fetched.

### Transaction 3: CASE-01-BUSSOLA-URL
- **Timestamp:** `2026-09-19T00:04:03.913212Z`
- **Client:** `192.168.1.54:51325` (`RECEIVER_HW`)
- **Request:** `GET /bussola/redirect?type=vod&user=035289282213&product=DSI74%20V2%20HD%20GVT&fw=RC1.12.12&sw=1.0.5 HTTP/1.1`
- **Host:** `191.32.31.251`
- **Case ID / Run ID:** `CASE-01-BUSSOLA-URL` / `CASE-01-BUSSOLA-URL-1789776186463060540`
- **Delivered Status:** `HTTP 200 OK` (81 bytes, No Location header)
- **Response SHA-256:** `e38a6e304263cf04be97fc37ae53af85bc98f27b2452009167abc0a75f111d94`
- **Observation:** Full 30.0s elapsed. Marker `/marker/bussola_c01_url` was not fetched.

---

## 4. Evidence Classification & Boundaries

| Milestone Level | Demonstrated? | Evidence Backing |
| :--- | :--- | :--- |
| **Response Delivered** | **YES** | Exact matching of Host, method, path, case_id, run_id, and response body SHA-256 on all 3 transactions |
| **Changed Application Behavior** | **YES** (UI banner) | Receiver clears live TV or displays connection error dialog |
| **Marker URL Fetched (via JSON field)** | **NO** | 0 requests to `/marker/bussola_c01_url` |
| **Marker URL Fetched (via HTTP 302)** | **NO** (in this run) | STB did not follow 302 to absolute URL `http://191.32.31.251/marker/bussola_c09_302` |
| **Document Visibly Rendered** | **NO** | Zero DOM/SVG rendering achieved in top-level viewport |
| **Supplied JavaScript Executed** | **NO** | Zero callbacks to `/report/script_exec` |
| **Native / System Capability** | **NO** | Zero execution or shell exposure |

### Evidence Constraints:
- TLS alert `unknown_ca` (48) proves only that the presented certificate chain was not trusted by the receiver; it does not establish an immutable, hardware-backed, or operator-only trust store.
- A client-side `JSON.parse()` exception remains a hypothesis explaining the error dialog; no runtime or application source traces confirm it directly.

---

## 5. Post-Session Verification & Cleanup Confirmation

Following session completion:
1. All run-owned processes (`arp_spoofer.py`, `http_interceptor.py`, `tcpdump`) terminated cleanly.
2. Custom iptables chains (`MNC005*`) were flushed and unlinked; no redirect rules remain in `PREROUTING`.
3. Sysctls restored: `net.ipv4.conf.all.send_redirects = 1`, `net.ipv4.conf.enp5s0.send_redirects = 1`.
4. Gateway reachability (`192.168.1.1`), DNS (`example.com`), and HTTPS egress verified passing.
