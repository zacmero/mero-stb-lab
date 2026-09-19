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
| **Response Delivered** | **YES** | Exact matching of Host, method, path, `case_id`, `run_id`, and response SHA-256 (`ed854de...`). |
| **HTTP 302 Followed by Hardware** | **YES** | Hardware requested `GET /portal.svg` exactly 21.7ms after receiving the 302 response. |
| **Target Marker Fetched** | **YES** | Served `web/portal.svg` (SVG Tiny 1.2, 1245 bytes) to `192.168.1.54:51349`. |
| **Document Visibly Rendered** | **PENDING** | Network-level fetch confirmed; display verification depends on physical screen or top-level viewport capture. |
| **Supplied JavaScript Executed** | **NO** | No callbacks to `/report/script_exec` observed. |
| **Native / System Capability** | **NO** | Zero execution or shell exposure. |

---

## 4. Post-Session Verification & Cleanup

- **Processes:** `rtk pgrep -af 'arp_spoofer.py|http_interceptor.py|tcpdump.*net-config-005'` confirmed zero active harness processes.
- **Firewall Rules:** `iptables-save` confirmed `MNC005*` chains deleted; no redirect rules in `PREROUTING`.
- **Sysctls:** `net.ipv4.conf.all.send_redirects = 1` and `net.ipv4.conf.enp5s0.send_redirects = 1` verified restored.
- **Network Health:**
  - Gateway reachable: `0.550 ms` avg round-trip time, 0% packet loss.
  - DNS resolution: `example.com` resolved.
  - HTTPS egress: `https://example.com/` succeeded (code 0).


---

## 5. Next Phase: Systematic Reduction of the Known-Positive Response

The historical positive is now treated as the control condition rather than as a hypothesis. The next phase changes one response property at a time while keeping the receiver, endpoint, trigger action, target path, and observation logic fixed.

### Core reduction sequence

| Case | Single intended change from the known-positive control | Question answered |
| :--- | :--- | :--- |
| `CASE-15-EXACT-HISTORICAL-D085` | None | Positive control: does `/portal.svg` still follow? |
| `CASE-16-HISTORICAL-HTTP11` | `HTTP/1.0` → `HTTP/1.1` | Is HTTP version part of the trigger? |
| `CASE-17-HISTORICAL-SERVER-GENERIC` | `Server: gvt-probe` → generic harness server value | Does the client depend on the historical Server header? |
| `CASE-18-HISTORICAL-NO-LOCATION` | Remove only the `Location` header | Can the historical JSON body trigger the follow-up without HTTP redirect semantics? |
| `CASE-19-302-LOCATION-MINIMAL-BODY` | Keep HTTP 302 + `Location`, remove all candidate navigation JSON keys | Is `Location` sufficient by itself? |

Run with:

```bash
python3 scripts/run_differential_campaign.py --sequence-reduction-core
```

Interpretation is intentionally differential:

- If CASE-16 fails while CASE-15 succeeds, HTTP/1.0 semantics become a required condition.
- If CASE-17 fails while CASE-15 succeeds, the historical `Server` header becomes a required condition.
- If CASE-18 still follows `/portal.svg`, one or more JSON fields can drive the follow-up without a `Location` header.
- If CASE-18 fails but CASE-19 succeeds, the evidence strongly isolates the HTTP 302 `Location` header as sufficient for the observed fetch, with the large JSON body unnecessary.

### JSON-key isolation sequence

If CASE-18 is positive, isolate candidate fields individually under the same HTTP/1.0 + 302 + no-`Location` envelope:

| Case | Candidate retained |
| :--- | :--- |
| `CASE-20-JSON-URL-ONLY` | `url` |
| `CASE-21-JSON-PORTALURL-ONLY` | `portalUrl` |
| `CASE-22-JSON-REDIRECTURL-ONLY` | `redirectUrl` |
| `CASE-23-JSON-VODURL-ONLY` | `vodUrl` |

Run with:

```bash
python3 scripts/run_differential_campaign.py --sequence-json-keys
```

This second sequence should only be treated as informative if the no-`Location` full historical JSON case is itself positive; otherwise the client has already told us that the HTTP redirect layer, rather than those JSON keys, explains the known follow-up fetch.
