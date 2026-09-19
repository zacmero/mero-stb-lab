# APP-API-009E: Comprehensive Runtime Capability Mapper

## Status

**COMPLETED — POSITIVE, LIMITED** on 2026-09-19.

APP-API-009E is a selectable mapper for the remaining stock Ekioh application surfaces. It replaces the inaccessible XHTML-in-`foreignObject` plugin experiment from APP-API-009D.

## Scope

The application records each result through receiver-authenticated HTTP reports. It provides six remote-selectable actions:

1. **Plugin construction and prototypes:** inspect the plugin and MIME registries, then create SVG, XHTML, plain-DOM, and SVG `embed` variants for `application/mozilla-npruntime-scriptable-plugin`. Reflect each element, lookup result, `object`, `contentDocument`, prototype chain, method arity, primitive value, and available property descriptor. It does not invoke discovered plugin methods.
2. **Ekioh and platform object graphs:** recursively reflect `ekiohPlatformInfo`, `SagemcomDFB`, connection-related globals, HTTP/XML constructors, and known Ekioh global functions through five prototype levels.
3. **Bounded connection signatures:** create connection objects using empty, URI, host/port, and protocol/host/port factory forms. Each object tries numeric-port, string-port, and explicit receiver-bound `call` forms against only `191.32.31.251:39009`, records state, and closes.
4. **DOM, XML, storage, and timers:** verify local/session storage and cookies, parse one in-memory XML document, reflect DOM objects, and test the two observed timer mechanisms.
5. **Full read-only inventory:** reflect `window`, `document`, `navigator`, `location`, `history`, and `screen`, including non-enumerable own properties where the runtime supports them.
6. **End network session:** close tracked connection objects and request harness cleanup. This does not exit the foreground Ekioh document. A cold reboot remains the only demonstrated exit.

## Boundaries

- No filesystem, USB, process, shell, firmware, power-state, or destructive platform method is invoked.
- Unknown native methods are reflected only.
- Connection attempts target only the experiment workstation.
- Tests run individually so a runtime failure can be attributed to one mapper.
- The network harness still requires exact receiver IP/MAC identity and performs its existing preflight, post-activation health check, and idempotent cleanup.

## Interactive sequence

1. Start the exact-target harness and wait for its health checks.
2. Cold reboot the receiver because APP-API-009D remains foreground.
3. Open Vivo Play once after normal television returns.
4. Wait for `Ready: choose a mapper`.
5. Select each action from 1 through 5. Wait for host-side result inspection after every action.
6. Select action 6 only after all evidence is captured.
7. Verify cleanup. Cold reboot only when the next application is ready.

## Hardware results

- The plugin/MIME registry advertised `Scriptability Demo Plugin`, but SVG, XHTML, plain-DOM, and SVG `embed` constructions exposed only ordinary DOM elements. Their `object` and `contentDocument` properties were undefined. No native module instance was obtained.
- The Ekioh transport, transport-server, transport-event, asynchronous-status, platform-information, HTTP, XML, and event-target surfaces were mapped through their prototype chains. No filesystem, shell, process, USB, or tuner bridge appeared.
- Four transport factory forms and three method-call forms produced native transport objects, but every call returned its native method object, remained disconnected, and emitted no SYN to the bounded workstation listener.
- `localStorage`, `sessionStorage`, cookies, XML parsing, DOM traversal, and `setTimeout` worked. `createTimer(25, callback)` rejected the callback because its second argument requires an integer.
- The full inventory created too many concurrent XHR reports. It reached `inventory-start` and 287 stored fields, then stopped before `inventory-complete`. This is a reporting-transport limit, not evidence that the later runtime roots are absent.

## Harness correction

Cold boot changed the receiver lease from `192.168.1.57` to `192.168.1.61`. The original sequence activated interception before reboot and therefore remained pinned to the old address. `run_net_config_005_after_boot.sh` now waits for a post-boot ARP/DHCP announcement, validates the exact MAC/IP pair, and only then starts interception. `run_net_config_005.sh` also treats an actively verified configured pair as authoritative over stale prior neighbor-cache entries.

RUNTIME-MAP-009F replaces concurrent per-property reports with a sequential bounded queue.
