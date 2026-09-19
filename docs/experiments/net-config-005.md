# Experiment Report: NET-CONFIG-005

## Metadata
- **Identifier:** `NET-CONFIG-005`
- **Date:** 2026-09-18
- **Target Hardware:** Sagemcom DSI74 V2 HD GVT (STMicroelectronics STiH237)
- **Status:** **COMPLETED (Historical Replay: CASE-15-EXACT-HISTORICAL-D085)**
- **Outcome:** **HISTORICAL POSITIVE REPRODUCED (/portal.svg FETCHED)**
- **Operating Constraint:** $0 Budget / Software & Ethernet Only

---

## 1. Executive Summary

```text
NET-CONFIG-005: Exact Historical Replay (CASE-15-EXACT-HISTORICAL-D085)
RESULT: HISTORICAL POSITIVE REPRODUCED. /portal.svg WAS FETCHED BY HARDWARE.

1. EXACT-TARGET HARNESS VERIFICATION:
   Single-target ARP redirection maintained between verified receiver (192.168.1.54, 
   68:15:90:6b:81:96) and gateway (192.168.1.1, 14:ca:56:81:18:71).
   Preflight and post-session health checks (gateway, DNS, HTTPS) all PASSED.

2. CASE-15 DELIVERY & IMMEDIATE FOLLOW-UP:
   Delivered exact historical response from commit d08504fb0325f5b36a46a375f31317483408f6ec:
   - Protocol: HTTP/1.0 302 Found
   - Headers: Server: gvt-probe, Location: /portal.svg,
              Content-Type: application/json; charset=utf-8,
              Access-Control-Allow-Origin: *, Connection: close
   - Body: 14-key JSON formatted with indent=2 (SHA-256: ed854de506008965...)
   - Delivery Timestamp: 2026-09-19T00:29:49.798672Z from 192.168.1.54:51348
   - Follow-up Request: Exactly 21.7 milliseconds later, at 2026-09-19T00:29:49.820381Z,
     RECEIVER_HW (192.168.1.54:51349) requested GET /portal.svg!
   - Response to Follow-up: HTTP/1.0 200 OK (image/svg+xml, 1245 bytes).

3. ANALYSIS OF PREVIOUS RUN LOGS:
   Inspection of the raw continuous capture (experiment_transactions.jsonl) revealed
   that the hardware followed all 302 redirects within 7-22 milliseconds:
   - CASE-12 (/portal.svg): followed at +20.7ms (00:17:27.652Z)
   - CASE-13 (/marker/bussola_c13_relative): followed at +18.9ms (00:19:08.633Z)
   - CASE-14 (/marker/bussola_c14_absolute): followed at +6.9ms (00:21:27.792Z)
   - CASE-15 (/portal.svg): followed at +21.7ms (00:29:49.820Z)
   The earlier differential evaluator consumed the subsequent transaction in Phase 1
   before Phase 2 reading commenced; this timing discrepancy in the test harness
   has been patched.

4. CONCLUSION:
   The historical positive is fully reproduced under the safe exact-target network harness.
   The STB receiver runtime faithfully follows HTTP 302 redirects to /portal.svg.
```

---

## 2. Hardware Transaction Log (`CASE-15-EXACT-HISTORICAL-D085`)

### Transaction 1: Trigger & 302 Redirect Delivery
- **Timestamp:** `2026-09-19T00:29:49.798672Z`
- **Client:** `192.168.1.54:51348` (`RECEIVER_HW`, MAC `68:15:90:6b:81:96`)
- **Request:** `GET /bussola/redirect?type=vod&user=035289282213&product=DSI74%20V2%20HD%20GVT&fw=RC1.12.12&sw=1.0.5 HTTP/1.1`
- **Request Headers:**
  - `User-Agent: Ekioh v2.2.4.5-sagem (Mar  2 2013) r10767`
  - `Host: 191.32.31.251`
  - `Connection: Keep-Alive`
  - `Accept-Encoding: gzip, deflate`
  - `Accept: application/json, text/plain, */*`
- **Run ID:** `CASE-15-EXACT-HISTORICAL-D085-1789777750716146812`
- **Delivered HTTP Version:** `HTTP/1.0`
- **Delivered HTTP Status:** `302 Found`
- **Delivered Response Headers:**
  ```http
  Server: gvt-probe
  Content-Length: 369
  Content-Type: application/json; charset=utf-8
  Location: /portal.svg
  Access-Control-Allow-Origin: *
  Connection: close
  ```
- **Delivered Serialized JSON Body (369 bytes):**
  ```json
  {
    "status": "ok",
    "code": 0,
    "url": "/portal.svg",
    "redirect": "/portal.svg",
    "redirectUrl": "/portal.svg",
    "portalUrl": "/portal.svg",
    "vodUrl": "/portal.svg",
    "target": "/portal.svg",
    "location": "/portal.svg",
    "destination": "/portal.svg",
    "result": {
      "url": "/portal.svg",
      "status": "ok"
    },
    "data": {
      "url": "/portal.svg"
    }
  }
  ```
- **Delivered Response SHA-256:** `ed854de506008965c8a569d6060b4c744597278544a2d3ad66ddfc7465c83e3b`

### Transaction 2: Follow-up Request for `/portal.svg`
- **Timestamp:** `2026-09-19T00:29:49.820381Z` (+21.71 ms delta)
- **Client:** `192.168.1.54:51349` (`RECEIVER_HW`, MAC `68:15:90:6b:81:96`)
- **Request:** `GET /portal.svg HTTP/1.1`
- **Request Headers:**
  - `User-Agent: Ekioh v2.2.4.5-sagem (Mar  2 2013) r10767`
  - `Host: 191.32.31.251`
  - `Connection: Keep-Alive`
  - `Accept-Encoding: gzip, deflate`
  - `Accept: application/json, text/plain, */*`
- **Delivered Status:** `HTTP/1.0 200 OK`
- **Delivered Content-Type:** `image/svg+xml; charset=utf-8`
- **Delivered Size:** `1245 bytes`
- **Delivered SHA-256:** `3a671e43c6ae0d355876cfd2a4d3664fc320667eff5ffce3b116f256bf34f061`

---

## 3. Evidence Classification Table

| Milestone Level | Demonstrated? | Backing & Constraints |
| :--- | :--- | :--- |
| **Response Delivered** | **YES** | Exact matching of Host, method, path, `case_id`, `run_id`, and response SHA-256 (`ed854de...` and `e3b0c44...`). |
| **HTTP 302 Followed by Hardware** | **YES** | Hardware requested `GET /portal.svg` (+19.03ms) and `GET /probe.svg` (+21.11ms). |
| **Response Body Reduction** | **YES** | A 0-byte payload (`Content-Length: 0`) produces the identical immediate redirect (+19ms). The 14-key JSON payload is 100% irrelevant. |
| **SVG Sub-resource Resolution** | **YES** | Receiver rendered `/probe.svg` and fetched `<image xlink:href="/marker/probe_subresource.png">` at +45.06ms. |
| **Supplied ECMAScript Executed** | **YES** | Receiver executed SVG embedded `<script>` tag: callbacks received via both `xhr` (+43.80ms) and `svg_getURL` (+44.50ms) from `192.168.1.54`. |
| **Document Visibly Rendered** | **INVESTIGATING** | Layout engine active (sub-resources resolved); physical screen display behavior under evaluation. |
| **Native / System Capability** | **NO** | Ekioh ECMAScript sandbox execution demonstrated; no host OS escape or shell exposure. |

---

## 4. Reduction & Capability Battery (CASE-16 & CASE-17)

### 4.1 CASE-16: Empty-Body Response Reduction (`CASE-16-302-EMPTY-BODY`)
- **Objective:** Determine if the 14-key JSON body is parsed or required by the redirect consumer.
- **Delivered Response:** `HTTP/1.1 302 Found`, `Location: /portal.svg`, `Content-Length: 0`, body: `b""` (0 bytes).
- **Delivery Timestamp:** `2026-09-19T01:15:35.792078Z` from `192.168.1.54:51362`.
- **Follow-up Request:** Exactly **19.03 milliseconds** later at `2026-09-19T01:15:35.811109Z`, `RECEIVER_HW` requested `GET /portal.svg`.
- **Finding:** The STB runtime redirects purely based on standard HTTP 302 status and `Location` header. The JSON payload is completely unnecessary.

### 4.2 CASE-17: Capability & Render Probe (`CASE-17-PORTAL-RENDER-PROBE`)
- **Objective:** Test if the followed document enters the Ekioh SVG layout/rendering engine and executes embedded scripts.
- **Trigger:** `GET /bussola/redirect` at `2026-09-19T01:21:35.917432Z`.
- **Delivered 302:** `Location: /probe.svg`, `Content-Length: 0`.
- **Transaction Cascade (Receiver IP: `192.168.1.54`):**
  1. `+21.11 ms` (`01:21:35.938542Z`): `GET /probe.svg` (Ekioh fetched SVG document).
  2. `+43.80 ms` (`01:21:35.982344Z`): `GET /report/script_exec?method=xhr` (Script execution via `XMLHttpRequest`!).
  3. `+44.50 ms` (`01:21:35.983039Z`): `GET /report/script_exec?method=svg_getURL` (Script execution via SVG Tiny 1.2 `getURL()`!).
  4. `+45.06 ms` (`01:21:35.983602Z`): `GET /marker/probe_subresource.png` (Layout engine fetched `<image>` subresource!).
  5. `+16.27 s` (`01:21:52.188731Z`): `GET /tv-config/appConfigFit.json` (Downstream middleware config fetch).
- **Verdict:** `SCRIPT_EXECUTION_DEMONSTRATED`.

---

## 5. Post-Session Verification & Cleanup

- **Processes:** `rtk pgrep -af 'arp_spoofer.py|http_interceptor.py|tcpdump.*net-config-005'` confirmed zero active harness processes.
- **Firewall Rules:** `iptables-save` confirmed `MNC005*` chains deleted; no redirect rules in `PREROUTING`.
- **Sysctls:** `net.ipv4.conf.all.send_redirects = 1` and `net.ipv4.conf.enp5s0.send_redirects = 1` verified restored.
- **Network Health:**
  - Gateway reachable: `0.520 ms` avg round-trip time, 0% packet loss.
  - DNS resolution: `example.com` resolved.
  - HTTPS egress: `https://example.com/` succeeded (HTTP 200).
