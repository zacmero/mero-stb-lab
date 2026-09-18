# Plan & Tracking: NET-CONFIG-005

## Metadata
- **Identifier:** `NET-CONFIG-005`
- **Date:** 2026-09-18
- **Target:** Sagemcom DSI74 V2 HD GVT (STiH237 / Ekioh Browser)
- **Status:** **IN PROGRESS**
- **Operating Constraint:** $0 Budget / Software & Network Only

---

## Objective

Deliver a structured JSON configuration response to the receiver's `/tv-config/appConfigFit.json` request, observe which configuration keys the Ekioh browser accepts, and serve a diagnostic HTML/SVG interface from the local workstation (`192.168.1.97`) to evaluate application-layer rendering on the TV display.

---

## Technical Architecture

```text
[ Sagemcom DSI74 V2 ]
  Browser: Ekioh v2.2.4.5-sagem
  1. Requests: GET /tv-config/appConfigFit.json HTTP/1.1
         │
         ▼ (via iptables port 80 redirect)
[ Host HTTP Server (192.168.1.97:8080) ]
  2. Responds with candidate portal URLs:
     {
       "status": "ok",
       "portalUrl": "http://192.168.1.97:8080/portal.html",
       "startUrl":  "http://192.168.1.97:8080/portal.html",
       "mainUrl":   "http://192.168.1.97:8080/portal.html"
     }
         │
         ▼
[ Sagemcom DSI74 V2 ]
  3. Parses JSON and requests next target: GET /portal.html HTTP/1.1
         │
         ▼
[ Host HTTP Server ]
  4. Delivers diagnostic HTML/SVG test page.
  5. Ekioh renders page on TV screen.
```

---

## Task Checklist

- [x] **Task 1: Prepare Candidate Configuration (`tv-config/appConfigFit.json`)**
  - Construct clean JSON containing standard Sagemcom/Ekioh portal and bootstrap keys.
- [x] **Task 2: Author Diagnostic Test Web Page (`web/portal.html` & `web/portal.svg`)**
  - Design high-contrast diagnostic page displaying "HELLO FROM THE GH05T" compatible with embedded SVG/HTML engines (Ekioh v2).
  - Include basic DOM / JavaScript clock to test client-side scripting.
- [x] **Task 3: Update HTTP Server for Multi-Path Serving**
  - Enhanced `scripts/http_interceptor.py` to route `/tv-config/appConfigFit.json`, `/portal.html`, `/portal.svg`, and capture all subsequent asset queries.
- [ ] **Task 4: Execute Live Session & Trigger STB**
  - Run session runner (`scripts/run_net_config_005.sh`).
  - Trigger cold boot or Portal button on STB remote.
  - Record subsequent HTTP requests and on-screen rendering.
- [ ] **Task 5: Compile Findings & Commit Reproducible Artifacts**
  - Document discovered schema keys, rendering status, and DOM capabilities in `docs/experiments/net-config-005.md`.

---

## Log of Findings & Observations

*(To be populated during live execution)*
