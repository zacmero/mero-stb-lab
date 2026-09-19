# APP-API-009C: Bounded Ekioh Connection Lab

## Objective

Determine whether the raw Ekioh globals discovered by APP-API-009B provide:

1. a receiver-initiated TCP client channel to the laboratory workstation;
2. an application-scoped TCP listener reachable from the workstation;
3. useful connection/server/plugin object methods beyond their global names.

This does not claim or attempt OS command execution. All live connection targets are restricted to the laboratory workstation and unprivileged ports `39009` and `39010`.

## Automatic reflection

On load, `web/app-api-009c.svg` records function type, declared arity, native string representation, own properties, prototype property names, and prototype member types for:

- `createConnection`, `createConnectionServer`, and `createTimer`;
- `Connection`, `ConnectionServer`, `Timer`, `ConnectionEvent`, and `AsyncURLStatus`;
- the `application/mozilla-npruntime-scriptable-plugin` MIME object and its `enabledPlugin` object.

Reflection completes before any connection factory is invoked.

## Selectable tests

### Run outbound TCP test

The app chooses one factory signature based on `createConnection.length` and targets only `191.32.31.251:39009`. It reflects the returned object, attaches bounded connection/data/error event handlers, invokes an exposed `connect` method only when present, and sends only `MERO-APP-API-009C\n` through the first exposed `send`, `write`, or `sendData` method.

The interceptor owns a threaded TCP evidence listener on port `39009`. It records timestamp, exact receiver identity classification, byte length, SHA-256, and a bounded text prefix, then returns `MERO-009C-REPLY\n` only to `RECEIVER_HW`.

### Start receiver listener

The app chooses one factory signature based on `createConnectionServer.length`, restricted to receiver port `39010`. It invokes `listen` or `start` only when that method is exposed. Once the result is recorded, the workstation makes one direct connection to the exact receiver IP on `39010`.

### Stop receiver listener

The app invokes the first exposed `close`, `stop`, or `shutdown` method. End Session calls this stop action before requesting host cleanup. If no stop method exists, the test ends and a cold reboot is required before any later network experiment.

### End Session

As in APP-API-009B, this requests verified host cleanup. It does not claim to close the receiver document.

## Local verification

- Bash and Python syntax: pass.
- SVG/XML and extracted JavaScript parsing: pass.
- `/launch.svg` redirects to `/app-api-009c.svg`: pass.
- APP-API-009C document route: HTTP 200 with no-store: pass.
- Raw TCP listener records bytes and SHA-256: pass.
- Simulated `RECEIVER_HW` receives the exact raw reply: pass.
- Local HTTP reports and End Session requests are rejected with HTTP 403: pass.
- TCP listener is closed after interceptor shutdown: pass.

## Hardware sequence

Do not reboot until the host says the application and harness are ready.

1. Cold reboot once.
2. Start the exact-target harness and wait for post-interception health PASS.
3. Open Vivo Play once and wait for `Reflection complete`.
4. Run the outbound TCP test once.
5. Start the receiver listener once; wait while the host probes exact port `39010`.
6. Stop the receiver listener once.
7. End Session once and wait for host cleanup confirmation.
8. Cold reboot only after cleanup, because the injected document still cannot exit natively.

## Hardware result — 2026-09-19

The verified receiver loaded the 12,539-byte APP-API-009C document. Its SHA-256 is `a22259b99c5e7c24b7ce78a2b86b97a7c0199af05db31627d00327e620ac2a53`. The durable result contains 169 observations; SHA-256 `879f7684e0b659c8959d442c2553733ce5383331b225ec9416c3f1796674b7a1`.

### Connection client object

- `createConnection.length` was `0`; `createConnection()` returned an object.
- Its prototype exposed `connected`, `timeout`, `asynchronous`, `connect`, `send`, `close`, and `receive`.
- `connect.length` was `2`. `connect("191.32.31.251", 39009)` returned without a synchronous exception.
- The capture contained no receiver TCP SYN to port `39009`; the host evidence listener received no receiver connection.
- A delayed `send("MERO-APP-API-009C\n")` raised `[object GlobalException]`, consistent with no established connection.

Verdict: **POSITIVE for a real raw connection API surface; NEGATIVE for the tested default-state outbound connection.** The next bounded test must inspect instance values/return values and method arities, then vary only documented-looking state such as `asynchronous`, `timeout`, and port representation. It must not broaden destinations.

### Connection server object

- `createConnectionServer.length` was `0`; `createConnectionServer()` returned an object.
- Its prototype exposed only `listen` and `close`; `listen.length` was `2`.
- `listen("0.0.0.0", 39010)` returned without a synchronous exception.
- The workstation sent four TCP SYNs to exact receiver port `39010`; no SYN-ACK or reset returned.
- The receiver reported `close:invoked` at `05:29:05.504748Z`, releasing any internal server state.

Verdict: **POSITIVE for an application-scoped server API surface; NO LAN-REACHABLE LISTENER demonstrated.** The result is compatible with wrong argument semantics, an internal-only bind, or the same inbound firewall observed by NETWORK-SERVICE-011.

### Plugin and boot capture

The scriptable plugin object exposed only `length`, `name`, `description`, `item`, and `namedItem`; no callable native bridge was found.

The separate passive cold-boot capture (`app-api-009c-boot-2.pcap`, SHA-256 `e38bdf7a5bebead9d53efd13bd0e554edcb9b791fa2cfd8e038446e5859470b5`) contains seven packets: receiver ARP for the gateway, the workstation's later exact ping/ARP, and the receiver reply. A switched LAN does not mirror receiver↔gateway unicast traffic, so this capture does not exclude boot-time outbound services.

### Cleanup

The verified receiver requested End Session at `05:30:46.312797Z`. All run-owned processes stopped, workstation ports `39009/39010` were closed, the receiver retained its correct IP/MAC mapping, gateway/DNS/HTTPS passed, and both `send_redirects` sysctls returned to `1`.
