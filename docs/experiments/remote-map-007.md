# REMOTE-MAP-007: Named Remote-Control Calibration

**Date:** 2026-09-19  
**Receiver:** Sagemcom DSI74 V2 HD GVT  
**Runtime:** Ekioh `v2.2.4.5-sagem`  
**Result:** **COMPLETED — 40/40 labels captured**

## Objective

Map each named OEM remote-control button to the DOM `keydown` code delivered by the receiver. Preserve observed mappings separately from earlier bulk-event inference.

## Safety and identity

The session used the NET-CONFIG-005 exact-target harness. Passive ARP discovery established `192.168.1.57` for receiver MAC `68:15:90:6b:81:96`. The runner independently populated the neighbor table and required that exact mapping before adding interception state.

After capture, the runner stopped its ARP redirector and HTTP interceptor, removed its firewall chains, and restored the original sysctl values. Gateway reachability, DNS, and HTTPS egress passed after cleanup.

## Protocol

1. The local controller activates calibration without arming a button.
2. Vivo Play loads `/remote-map.svg`.
3. The receiver calls `/remote-map/ready`.
4. Only after that callback does the controller arm the first label. This prevents the Vivo Play launch event from being recorded as `UP`.
5. The receiver accepts only one `keydown` while one label is armed.
6. The interceptor writes each observed mapping atomically to `captures/remote-map-007.json`.
7. The controller advances through the fixed 40-label sequence and resets to `idle` after completion.

Earlier invalid runs are retained as `captures/remote-map-007.superseded-*.json` evidence and are excluded from the canonical mapping.

## Canonical mapping

The machine-readable mapping is [`web/remote_keymap.json`](../../web/remote_keymap.json).

| Button | Decimal | Hex |
|---|---:|---:|
| UP | 38 | `0x26` |
| DOWN | 40 | `0x28` |
| LEFT | 37 | `0x25` |
| RIGHT | 39 | `0x27` |
| OK | 13 | `0x0D` |
| BACK | 917536 | `0xE0020` |
| EXIT | 917760 | `0xE0100` |
| HOME | 36 | `0x24` |
| MENU | 917555 | `0xE0033` |
| GUIDE | 917776 | `0xE0110` |
| INFO | 917556 | `0xE0034` |
| RED | 917504 | `0xE0000` |
| GREEN | 917505 | `0xE0001` |
| YELLOW | 917506 | `0xE0002` |
| BLUE | 917507 | `0xE0003` |
| 0–9 | 48–57 | `0x30`–`0x39` |
| PLAY / PAUSE | 917528 | `0xE0018` |
| STOP | 917522 | `0xE0012` |
| RECORD | 917527 | `0xE0017` |
| REWIND / PREVIOUS | 917523 | `0xE0013` |
| FAST_FORWARD / NEXT | 917524 | `0xE0014` |
| VOLUME_UP | 917747 | `0xE00F3` |
| VOLUME_DOWN | 917748 | `0xE00F4` |
| MUTE | 917744 | `0xE00F0` |
| CHANNEL_UP | 917552 | `0xE0030` |
| CHANNEL_DOWN | 917553 | `0xE0031` |
| VIVO_PLAY | 917778 | `0xE0112` |
| PORTAL | 917554 | `0xE0032` |

PLAY/PAUSE, REWIND/PREVIOUS, and FAST_FORWARD/NEXT are combined physical controls and intentionally share codes.

## Display defect and correction

The receiver repeatedly fetched the correct plain-text state, including `armed|UP||`, but direct text-node mutation remained visually stale at `WAITING FOR TERMINAL`. Capture continued correctly, and the operator used the state endpoint as the reference.

The corrected mapper refreshes `/remote-map/frame.svg` as an SVG image subresource. APP-RUNTIME-006 demonstrated this mechanism across 191 distinct frame requests. The mapper-specific correction is implemented but awaits the next hardware session.

## Application exit behavior

APP-EXIT-008 tested Vivo Play code `917778` (`0xE0112`) as an application-exit toggle and produced a **negative** result. Vivo Play reached JavaScript, but browser close and history operations did not return to native television. Remote and physical power controls also failed while the injected top-level document was active. Cold power removal remains the only demonstrated escape, and Vivo Play remains available as a normal mapped application button.

## Evidence boundary

REMOTE-MAP-007 demonstrates named DOM key codes and a complete calibration transaction path. It does not demonstrate native operating-system access, native media playback, persistent receiver modification, or an application-controlled exit path.
