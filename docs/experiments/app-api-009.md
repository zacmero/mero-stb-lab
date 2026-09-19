# APP-API-009: Ekioh Runtime Capability Inventory

**Date:** 2026-09-19  
**Receiver:** Sagemcom DSI74 V2 HD GVT  
**Runtime:** Ekioh `v2.2.4.5-sagem`  
**Result:** **COMPLETED — POSITIVE, LIMITED**

## Objective

Inventory read-only browser and vendor runtime surfaces that might bridge the demonstrated SVG/ECMAScript application environment to media, storage, USB, lifecycle, or operating-system capabilities.

## Demonstrated capabilities

The receiver executed APP-API-009 and delivered durable reports to `captures/app-api-009.json`.

| Surface | Observed value |
|---|---|
| `navigator.platform` | `SagemcomDFB` |
| `XMLHttpRequest` | `function` |
| `getURL` | `function` |
| `localStorage` | `object` |
| `sessionStorage` | `object` |
| `ekiohPlatformInfo` | `object`, no enumerable members |
| `WebSocket` | `undefined` |
| `Worker` | `undefined` |
| `FileReader` | `undefined` |
| `indexedDB` | `undefined` |
| `openDatabase` | `undefined` |
| `applicationManager` | `undefined` |
| `oipfObjectFactory` | `undefined` |
| `broadcast` / `dvb` | `undefined` |
| `media` | `undefined` |
| `usb` | `undefined` |

This supports network-backed thin-client applications and browser-local key/value storage. It does not expose a shell, filesystem, native process execution, media pipeline, DVB controller, or USB API through the tested globals.

## Visual behavior

The static APP-API-009 document rendered correctly. The receiver fetched changing `/app-api/frame.svg` resources continuously, but did not visibly composite those refreshed SVG image resources over the top-level document. Network fetches alone therefore do not establish visible refreshed-frame rendering on this application.

## APP-EXIT-008 result

The calibrated Vivo Play code `917778` reached the application and emitted `exit=vivo_play` three times. The following operations did not leave the injected top-level document:

- `window.close()`;
- `top.close()`;
- `window.open("", "_self")` followed by close;
- `window.history.back()`;
- `window.history.go(-4)`.

The remote power button and physical front-panel power button also did not exit or shut down the receiver while the injected document was active. Cold power removal is the only demonstrated recovery.

## Operational rule

Future live application tests must be bundled into one planned session. The harness must be cleaned up before cold power removal. Do not promise an in-application exit until a receiver-native lifecycle API is demonstrated.

## Follow-up status

APP-API-009B, APP-API-009C, MEDIA-010, and NETWORK-SERVICE-011 are complete. Deep reflection found real Ekioh connection/server objects and a scriptable-plugin MIME, but no native process, filesystem, USB, or OS-command bridge. See `app-api-009b-media-010.md`, `app-api-009c.md`, and `network-service-011.md` for the bounded evidence and cleanup results.
