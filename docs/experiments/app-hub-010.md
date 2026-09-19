# APP-HUB-010: Persistent In-App Experiment Hub

## Status

**COMPLETED — POSITIVE for in-session module replacement.**

On 2026-09-19, receiver `192.168.1.62` (MAC `68:15:90:6b:81:96`) loaded one stable foreground SVG and polled a versioned manifest every two seconds. The receiver loaded module v1, then loaded module v2 without a reboot, another remote action, or replacement of the top-level document.

This is session persistence, not OS or boot persistence. A cold boot still requires the exact-device network harness and one Vivo Play launch.

## Design

1. `/launch.svg` redirects to `/app-hub.svg`.
2. The hub polls `/app-hub-manifest.json` with cache-busting query data.
3. A changed `version` causes the hub to fetch and evaluate the named module.
4. Modules receive a small API for status text and evidence reporting.
5. `localStorage["mero_hub_runs"]` records execution across module versions.
6. Setting manifest `cleanup` to `true` requests `/app-api/end-session`.

The committed manifest has `cleanup: false`. This prevents a future launch from immediately terminating its harness.

## Hardware evidence

Module v1 reported:

- `module.v1.executed = count=1`
- `module.v1.timerFactory = function`
- `module.v1.transportFactory = function`
- `hub.module.loaded = hub-module-v1`

The workstation then changed only the module and manifest version. Module v2 reported:

- `module.v2.executed = count=2`
- `module.v2.document = svg`
- `module.v2.location = http://191.32.31.251/app-hub.svg`
- `hub.module.loaded = hub-module-v2`

These receiver-originated reports demonstrate code replacement inside the existing foreground document and retained local storage. The user did not confirm a visible text repaint on the TV, so visible repaint remains unproven. A transient `hub.module.http = 0` occurred while the module file was being replaced, but the next poll loaded v2 successfully.

Final committed asset hashes:

- `app-hub.svg`: `d366d9dd3cc2b0a5170d28ad8bdf89bd261c9b87ab83e77e70f8c52f79fb597f`
- `app-hub-module.js` (v2): `0a985596f7cf0f36eab6fc10d8414793499d465058c71b103eb69ff7de0cd482`
- `app-hub-manifest.json`: `3b916521af0e1bd32b0d37eeb7e4e4b2cb0e2a33cf19b9d6be42a268a02da771`

## Cleanup verification

Manifest-controlled cleanup stopped the ARP redirector, interceptor, and packet capture. Verification found zero `MNC005` firewall rules. Both `send_redirects` sysctls returned to `1`. The gateway responded with zero packet loss, DNS resolved `example.com`, and an HTTPS request to `https://example.com/` succeeded.

## Boundary and next use

APP-HUB-010 reduces future experiments to module and manifest updates while the hub remains open. It does not establish filesystem access, shell execution, startup persistence, native-service installation, boot-image replacement, or access outside the application runtime.

Future application-runtime probes should run as hub modules and use receiver-originated reports as canonical evidence. A module should request cleanup only after its final report has been delivered.
