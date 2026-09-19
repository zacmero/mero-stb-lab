# APP-API-009D: Connection State and Native Plugin Probe

## Status

**COMPLETED — POSITIVE, LIMITED** on 2026-09-19.

The receiver preserved application-origin `localStorage` across a cold boot. The exposed Ekioh connection object was real and inspectable, but neither tested call form initiated a TCP connection. The attempted XHTML plugin element was unavailable through the SVG Tiny DOM, so native plugin instantiation remains unresolved.

## Objective

Resolve three APP-API-009C boundaries:

1. Test the observable state of the Ekioh connection object in synchronous and asynchronous configurations.
2. Verify whether application-origin storage survives a cold boot.
3. Reflect an instantiated `application/mozilla-npruntime-scriptable-plugin` object without invoking unknown methods.

All connection attempts were restricted to the laboratory workstation at `191.32.31.251:39009`. The application did not request filesystem, process, device, firmware, or privileged OS operations.

## Test identity

- Receiver IPv4: `192.168.1.57`
- Receiver MAC: `68:15:90:6b:81:96`
- User agent: `Ekioh v2.2.4.5-sagem (Mar 2 2013) r10767`
- Application request: `2026-09-19T19:06:44.967095Z`
- Application SHA-256: `ffdb3da9bd6627d538c26648976661c543a67da02f11cab16316afffb5c6d6c8`
- Result record: 102 fields
- Result SHA-256: `ddd55454d61876aaf73af944c91b957249b0907bae79ec54ec4f68b13a746d81`
- Packet capture SHA-256: `15e7c75f0d28cbc368d7f3265bbf55b55134afdcacbe85e271550964ab18486a`

## Results

### Cross-boot storage persistence: positive

`localStorage` returned the previous marker `946688483259`, written during APP-API-009B before the latest cold boot. This demonstrates persistent application-origin key/value storage across receiver reboots. It does not demonstrate arbitrary filesystem access, boot persistence, or automatic application launch.

### Ekioh connection object: present, no connection initiated

Both objects exposed this prototype surface:

```text
connected, timeout, asynchronous, connect, send, close, receive
```

Observed method arities were `connect.length=2`, `send.length=1`, `receive.length=0`, and `close.length=0`. Initial state was `connected=false`, `timeout=100`, and `asynchronous=true`.

Setting `timeout=3` succeeded. Setting `asynchronous=false` did not persist; the property remained `true`. Both `connect("191.32.31.251", 39009)` and the string-port variant returned a native `connect` function representation rather than a connection result. `connected` remained false, including all 12 asynchronous polls over three seconds. No SYN reached the workstation, and the raw listener recorded no connection.

This establishes that the wrapper exists and exposes state. It does not establish the correct invocation semantics. The return value is consistent with an API binding or calling-convention mismatch, but it does not identify which argument form the firmware expects.

### Native plugin reflection: inconclusive

The application inserted an XHTML `<object>` with MIME type `application/mozilla-npruntime-scriptable-plugin` inside an SVG `foreignObject`. The load report identified an object element, but explicit reflection returned `TypeError: element is null` for both the object and its `contentDocument`.

This shows that the chosen XHTML-in-SVG construction did not remain accessible through this SVG Tiny DOM. It does not prove that the advertised plugin is unavailable. A later probe should use an SVG-native or dynamically created object element and remain reflection-only until an object is obtained.

## Cleanup and network health

The receiver selected End Session at `2026-09-19T19:15:07.818778Z`; `/app-api/end-session` returned HTTP 200 at `2026-09-19T19:15:07.820930Z`.

After cleanup:

- no `arp_spoofer.py`, `http_interceptor.py`, or experiment `tcpdump` process remained;
- no listener remained on ports 80, 8080, or 39009;
- the receiver still mapped uniquely to `68:15:90:6b:81:96`;
- gateway ping, DNS resolution, and HTTPS egress passed;
- `net.ipv4.conf.all.send_redirects` and `net.ipv4.conf.enp5s0.send_redirects` were restored to `1`.

## Conclusion

APP-API-009D adds one durable capability: receiver applications can retain state across cold boots through origin-scoped `localStorage`. It did not produce a TCP session, an inbound service, a boot-time service, terminal access, or native plugin access. The next narrow experiment is APP-API-009E: determine the correct DOM construction for the advertised scriptable plugin and reflect it without invoking unknown methods.
