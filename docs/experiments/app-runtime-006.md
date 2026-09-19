# Experiment Report: APP-RUNTIME-006

## Metadata

- **Identifier:** `APP-RUNTIME-006`
- **Date:** 2026-09-19
- **Target:** Sagemcom DSI74 V2 HD GVT, stock Ekioh v2.2.4.5-sagem runtime
- **Status:** **COMPLETED**
- **Outcome:** **POSITIVE — DYNAMIC FOREGROUND APPLICATION AND REMOTE INPUT DEMONSTRATED**
- **Prerequisite:** `NET-CONFIG-005` exact-target network harness and foreground navigation milestone

## 1. Objective

Determine which application primitives are usable after navigating the stock receiver into a custom foreground SVG document. Test independent animation, timer, DOM mutation, network polling, refreshed subresources, and remote-control input mechanisms without claiming native operating-system access.

## 2. Delivery Chain

The safe NET-CONFIG-005 harness intercepted only the verified receiver `192.168.1.54` (`68:15:90:6b:81:96`). The established chain remained:

```text
Vivo Play
  → GET /bussola/redirect
  → HTTP 302 Location: /portal.svg
  → /portal.svg executes supplied ECMAScript
  → window.location.href = /app.svg
  → foreground runtime diagnostics application
```

The receiver fetched `web/app.svg` at `2026-09-19T02:17:01.913925Z`:

- HTTP status: `200`
- Content type: `image/svg+xml; charset=utf-8`
- Size: `7290` bytes
- SHA-256: `48e352b35659aa3b802d22823f6e6c0a0456bc0784028996af85c03dd55f1c38`

At `02:17:02.418175Z`, the application emitted `target=runtime_lab&method=loaded`, proving that its supplied ECMAScript executed.

## 3. Runtime Matrix

The foreground application tested seven independent capability groups.

| Probe | Mechanism | Network evidence | Visual evidence | Result |
|---|---|---|---|---|
| Native animation | SVG Tiny `<animate>` on color and radius | Not applicable | Changing colors were observed, although the user did not separately identify the SMIL and refreshed-image panels | **Consistent with success; not isolated** |
| Recursive timer | `window.setTimeout()` recursion | `timeout_attribute` callback at tick 1 and continued frame/state sequence growth | Numbers changed | **Demonstrated** |
| Attribute mutation | `setAttribute("x", ...)` | `timeout_attribute` callback | Dynamic screen activity observed | **Demonstrated by execution evidence; individual motion not separately reported** |
| Text mutation | `firstChild.data` and `textContent` | Both callbacks received at tick 1 | Numbers changed | **Demonstrated** |
| HTTP polling | Repeated `XMLHttpRequest` to `/runtime/state` | `xhr_poll status=200`; 219 total state requests across XHR and `getURL()` | Numbers changed | **Demonstrated** |
| SVG callback polling | Repeated `getURL()` to `/runtime/state` | `getURL_poll callback` received | Application remained active | **Demonstrated** |
| Refreshed image | Repeated `xlink:href` changes to `/runtime/frame.svg?seq=N` | 191 distinct frame requests observed | Changing colors and numbers observed | **Demonstrated** |

Initial evidence arrived within approximately 1.4 seconds of `/app.svg` delivery:

- `02:17:02.872685Z`: recursive timeout and attribute callback
- `02:17:02.873191Z`: `firstChild.data` callback
- `02:17:02.873589Z`: `textContent` callback
- `02:17:02.873956Z`: refreshed frame 1 fetched
- `02:17:03.068813Z`: XHR state request returned HTTP 200
- `02:17:03.100612Z`: XHR callback confirmed
- `02:17:03.277786Z`: `getURL()` state request returned HTTP 200
- `02:17:03.309823Z`: `getURL()` callback confirmed

No runtime error callback was recorded for these mechanisms.

## 4. Continuous-Application Result

The stale clock in the earlier foreground proof did not indicate a general timer or DOM limitation. APP-RUNTIME-006 demonstrated a working continuous-update model using recursive `setTimeout()` calls.

During the observed session, the receiver issued:

- `191` requests for sequential `/runtime/frame.svg` documents;
- `219` requests to `/runtime/state` through XHR and SVG `getURL()`;
- monotonically increasing sequence values reaching at least `129` in the inspected interval;
- distinct response hashes as frame numbers, colors, and server timestamps changed.

This supports continuously updated dashboards, menus, status displays, low-rate image streams, and PC-backed thin-client applications. It does not yet establish acceptable frame rate for full-motion video. Native media-pipeline testing remains separate.

## 5. Remote-Control Input

The receiver delivered standard DOM keyboard events to supplied ECMAScript. The session recorded:

- `51` physical button presses;
- `153` callbacks;
- `35` distinct key codes;
- a complete `keydown`, `keypress`, and `keyup` sequence for every captured press.

### 5.1 Confirmed Standard Mappings

| Decimal | Hex | Mapping |
|---:|---:|---|
| `13` | `0x000D` | OK / Enter |
| `36` | `0x0024` | Home |
| `37` | `0x0025` | Left |
| `38` | `0x0026` | Up |
| `39` | `0x0027` | Right |
| `40` | `0x0028` | Down |
| `49`–`57` | `0x0031`–`0x0039` | Digits 1–9 |

Digit `0` (`48`) was not present in the captured set.

### 5.2 Private Ekioh Codes

The following 22 distinct media/service codes were captured:

```text
0xE0000  0xE0001  0xE0002  0xE0003  0xE0005
0xE0012  0xE0013  0xE0014  0xE0015  0xE0017  0xE0018
0xE0020
0xE0030  0xE0031  0xE0033  0xE0034
0xE00F3  0xE00F4
0xE0100
0xE0110  0xE0112  0xE0114
```

These codes are verified observations, but their physical labels are not established because the bulk test did not record which named button was pressed at each timestamp. Assigning Play, Pause, Stop, Record, colored keys, Guide, Info, Back, Exit, Volume, or Channel labels from code order would be speculation.

## 6. Capability Boundary

APP-RUNTIME-006 demonstrates:

- foreground custom SVG rendering;
- supplied ECMAScript execution;
- recurring timers;
- dynamic SVG attributes and text;
- continuous HTTP polling;
- refreshed subresources;
- remote-control input suitable for interactive applications.

It does **not** demonstrate:

- native Linux process execution;
- shell or filesystem access;
- privilege escalation or escape from the Ekioh runtime;
- persistence without the network harness;
- native hardware-decoded video playback.

## 7. Next Experiment

`REMOTE-MAP-007` will calibrate one named button at a time. The screen will display the received decimal and hexadecimal code, while the operator follows a fixed prompt sequence. The resulting verified associations will be written to `web/remote_keymap.json` and used by an application launcher.

The calibration must distinguish observed mappings from inferred mappings and must not assign a label unless the named prompt and resulting event occur in the same calibration step.

