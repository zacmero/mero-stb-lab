# Experiment Report: NET-CONFIG-005

## Metadata
- **Identifier:** `NET-CONFIG-005`
- **Date:** 2026-09-18
- **Target Hardware:** Sagemcom DSI74 V2 HD GVT (STMicroelectronics STiH237)
- **Status:** **COMPLETED (Redirect Investigation Series)**
- **Outcome:** **NO NEW CAPABILITY DEMONSTRATED**
- **Operating Constraint:** $0 Budget / Software & Ethernet Only

---

## 1. Executive Summary

```text
NET-CONFIG-005: Redirect Investigation Series (CASE-12, CASE-13, CASE-14)
RESULT: NO NEW CAPABILITY DEMONSTRATED.

1. EXACT-TARGET HARNESS VERIFICATION:
   Strict single-target ARP redirection maintained exclusively between the verified
   receiver (192.168.1.54, 68:15:90:6b:81:96) and gateway (192.168.1.1, 14:ca:56:81:18:71).
   All preflight and post-interception health checks on gateway, DNS, and HTTPS
   passed with zero disruption to host networking.

2. CASE-12-HISTORICAL-PORTAL:
   Delivered HTTP 302 Found with Location: /portal.svg to RECEIVER_HW.
   Verified response SHA-256 (1d5b09e807c8c9b7...).
   Observed for a full 30.0s post-delivery window.
   Receiver did NOT request /portal.svg.
   Verdict: 302 delivered; no marker request observed.

3. CASE-13-302-RELATIVE:
   Delivered HTTP 302 Found with Location: /marker/bussola_c13_relative.
   Verified response SHA-256 (1d5b09e807c8c9b7...).
   Observed for a full 30.0s post-delivery window.
   Receiver did NOT request /marker/bussola_c13_relative.
   Verdict: 302 delivered; no marker request observed.

4. CASE-14-302-ABSOLUTE:
   Delivered HTTP 302 Found with Location: http://191.32.31.251/marker/bussola_c14_absolute.
   Verified response SHA-256 (1d5b09e807c8c9b7...).
   Observed for a full 30.0s post-delivery window.
   Receiver did NOT request /marker/bussola_c14_absolute.
   Verdict: 302 delivered; no marker request observed.

5. COMPARATIVE SYNTHESIS & INTERPRETATION:
   None followed.
   Per the experimental decision matrix:
   "none followed -> historical redirect behavior was context-dependent or previously misattributed."
   Because relative redirect handling was not confirmed, the gated JSON relative
   field test (Step 7) was not executed.
```

---

## 2. Redirect Investigation Results Table

| Case ID | Target Endpoint | Redirect Type & Location Tested | HTTP Status Delivered | Expected Marker | Marker Hit | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`CASE-12-HISTORICAL-PORTAL`** | `/bussola/redirect` | Relative path (`/portal.svg`) | HTTP 302 (`Location: /portal.svg`) | `/portal.svg` | False | **`302 delivered; no marker request observed`** |
| **`CASE-13-302-RELATIVE`** | `/bussola/redirect` | Relative marker (`/marker/bussola_c13_relative`) | HTTP 302 (`Location: /marker/...`) | `/marker/bussola_c13_relative` | False | **`302 delivered; no marker request observed`** |
| **`CASE-14-302-ABSOLUTE`** | `/bussola/redirect` | Absolute URL (`http://191.32.31.251/marker/...`) | HTTP 302 (`Location: http://...`) | `/marker/bussola_c14_absolute` | False | **`302 delivered; no marker request observed`** |

---

## 3. Verified Hardware Transactions (from `captures/differential_results.json`)

### Transaction 1: CASE-12-HISTORICAL-PORTAL
- **Timestamp:** `2026-09-19T00:17:27.632016Z`
- **Client:** `192.168.1.54:51332` (`RECEIVER_HW`, MAC `68:15:90:6b:81:96`)
- **Request:** `GET /bussola/redirect?type=vod&user=035289282213&product=DSI74%20V2%20HD%20GVT&fw=RC1.12.12&sw=1.0.5 HTTP/1.1`
- **Host:** `191.32.31.251`
- **Run ID:** `CASE-12-HISTORICAL-PORTAL-1789776990300197973`
- **Delivered Status:** `HTTP 302 Found` (22 bytes, `Location: /portal.svg`)
- **Response SHA-256:** `1d5b09e807c8c9b7e8c620110533ee77483729c9ac1107898aeda548ef95540e`
- **Observation:** Full 30.0s elapsed post-delivery. Zero follow-up requests for `/portal.svg`.

### Transaction 2: CASE-13-302-RELATIVE
- **Timestamp:** `2026-09-19T00:19:08.614499Z`
- **Client:** `192.168.1.54:51336` (`RECEIVER_HW`, MAC `68:15:90:6b:81:96`)
- **Request:** `GET /bussola/redirect?type=vod&user=035289282213&product=DSI74%20V2%20HD%20GVT&fw=RC1.12.12&sw=1.0.5 HTTP/1.1`
- **Host:** `191.32.31.251`
- **Run ID:** `CASE-13-302-RELATIVE-1789777099639096165`
- **Delivered Status:** `HTTP 302 Found` (22 bytes, `Location: /marker/bussola_c13_relative`)
- **Response SHA-256:** `1d5b09e807c8c9b7e8c620110533ee77483729c9ac1107898aeda548ef95540e`
- **Observation:** Full 30.0s elapsed post-delivery. Zero follow-up requests for `/marker/bussola_c13_relative`.

### Transaction 3: CASE-14-302-ABSOLUTE
- **Timestamp:** `2026-09-19T00:21:27.786046Z`
- **Client:** `192.168.1.54:51340` (`RECEIVER_HW`, MAC `68:15:90:6b:81:96`)
- **Request:** `GET /bussola/redirect?type=vod&user=035289282213&product=DSI74%20V2%20HD%20GVT&fw=RC1.12.12&sw=1.0.5 HTTP/1.1`
- **Host:** `191.32.31.251`
- **Run ID:** `CASE-14-302-ABSOLUTE-1789777198789369671`
- **Delivered Status:** `HTTP 302 Found` (22 bytes, `Location: http://191.32.31.251/marker/bussola_c14_absolute`)
- **Response SHA-256:** `1d5b09e807c8c9b7e8c620110533ee77483729c9ac1107898aeda548ef95540e`
- **Observation:** Full 30.0s elapsed post-delivery. Zero follow-up requests for `/marker/bussola_c14_absolute`.

---

## 4. Evidence Classification & Boundaries

| Milestone Level | Demonstrated? | Backing & Constraints |
| :--- | :--- | :--- |
| **Response Delivered** | **YES** | Exact matching of Host, method, path, `case_id`, `run_id`, and response body SHA-256 for all 3 transactions. |
| **Changed Application Behavior** | **YES** (UI banner) | Receiver displays connection error dialog or clears live TV window upon 302 response. |
| **Marker Fetched (via Relative 302)** | **NO** | 0 requests observed for `/portal.svg` or `/marker/bussola_c13_relative`. |
| **Marker Fetched (via Absolute 302)** | **NO** | 0 requests observed for `/marker/bussola_c14_absolute`. |
| **Document Visibly Rendered** | **NO** | Zero DOM/SVG top-level rendering achieved. |
| **Script Executed** | **NO** | Zero execution callbacks received (`/report/script_exec`). |
| **Native Capability Exposed** | **NO** | Zero command execution or shell capability exposed. |

### Technical Analysis & Disconfirmation:
1. **Redirect Follow Mechanism Disconfirmed on `/bussola/redirect`:**
   The receiver's HTTP client for `/bussola/redirect` (identified by User-Agent `Ekioh v2.2.4.5-sagem (Mar  2 2013) r10767`) is an XHR/API consumer expecting JSON data. It does not automatically follow HTTP 302 redirects, whether relative (`/portal.svg`, `/marker/...`) or absolute (`http://...`).
2. **Historical Misattribution:**
   Historical claims that `/portal.svg` was fetched following a 302 redirect were context-dependent (e.g., triggered during initial boot splash or alternative UI invocation) or misattributed in prior untargeted interception sessions.
3. **Step 7 Guard Condition:**
   Because relative redirects were not followed, generic relative navigation via JSON fields was not unlocked.

---

## 5. Post-Session Verification & Cleanup Confirmation

Following session completion:
1. All run-owned processes (`arp_spoofer.py`, `http_interceptor.py`, `tcpdump`) terminated cleanly. Zero lingering processes confirmed via `pgrep`.
2. Custom iptables chains (`MNC005*`) were flushed and unlinked; no redirect rules remain in `PREROUTING`.
3. Sysctls restored: `net.ipv4.conf.all.send_redirects = 1`, `net.ipv4.conf.enp5s0.send_redirects = 1`.
4. Host network health verified:
   - Gateway ping (`192.168.1.1`): `0.534 ms` avg, 0% loss.
   - DNS resolution (`example.com`): PASSED.
   - HTTPS egress (`https://example.com/`): PASSED (code 0).
