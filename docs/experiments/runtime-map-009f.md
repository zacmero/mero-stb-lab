# RUNTIME-MAP-009F: Sequential Capability Mapper

## Status

**COMPLETED — POSITIVE** on 2026-09-19.

## Purpose

APP-API-009E demonstrated that the receiver's old HTTP runtime can stall when an application creates thousands of concurrent result requests. RUNTIME-MAP-009F keeps one result request active at a time and compresses property observations into bounded chunks.

## Automatic tests

1. **Runtime surfaces:** maps property names for `window`, `document`, `navigator`, optional location/history/screen objects, platform information, and the known transport/event objects through four prototype levels. Broad objects are names-only because APP-API-009F v2 identified a blocking global getter. Each result chunk is at most 900 characters.
2. **Safe data helpers:** performs a fixed string/binary round trip and reads heap/profiling values without changing device state.
3. **Integer timer variants:** tests four bounded two-integer forms derived from APP-API-009E's explicit conversion error. Returned values are reflected; no unknown returned method is invoked.
4. **Automatic cleanup:** after all three result queues drain, the application records `automatic.result=complete` and requests verified harness cleanup. It does not close the foreground receiver document.

## Reporting contract

- Results use sequential form-encoded POST requests to `/runtime-map-009f/report`.
- The next result is sent only after the prior request reaches ready state 4.
- The screen displays pending and delivered counts.
- The application waits for `Queue: 0 pending` before starting each next test.
- Reports are accepted only from the verified receiver identity.

## Launch procedure

1. Start `sudo scripts/run_net_config_005_after_boot.sh 3600` before or after the receiver boots.
2. The launcher polls only remembered exact receiver leases and validates the target MAC. It never scans a subnet.
3. Wait for `READY FOR CASE-00`.
4. Open Vivo Play once.
5. The application runs all tests and requests cleanup automatically. No remote navigation is required.
6. Verify the screen reaches `COMPLETE` and the host confirms cleanup.

When the receiver is stuck in a previous foreground document, start the launcher with `REQUIRE_RECEIVER_OFFLINE=1`. It waits for two consecutive offline checks before accepting a live lease, which guarantees interception is installed after the cold reboot rather than before it.

## Hardware result

The verified receiver loaded `RUNTIME-MAP-009F-v3-safe-auto` from post-boot address `192.168.1.62`. All phases completed without remote navigation:

- `surfaces-start` through `surfaces-complete`;
- `helpers-start` through `helpers-complete`;
- `timers-start` through `timers-complete`;
- `automatic.result=complete`;
- automatic End Session and verified harness cleanup.

The sequential queue delivered 77 result fields. Broad surface enumeration completed after value reads were removed from the names-only pass. This confirms that the prior stall came from dereferencing a blocking global property, not from enumeration or HTTP delivery.

The runtime reported `jsHeapUsed=159744`, `jsHeapMax=50331648`, and `profiling=false`. `stringToBinary("MERO-009F")` returned `TypeError: stringToBinary requires more than 1 argument`, so its full signature remains unresolved.

All four integer `createTimer` variants returned objects exposing:

```text
delay, repeatInterval, running, start, stop
```

No timer method was invoked. The result establishes a controllable native timer surface but not its event behavior.

## Evidence

- Application SHA-256: `14a346aba9db04acdc90ab8444f9ea62a93873cc8862eaf3c32b65d7d9936cfc`
- Result SHA-256: `11103460dfb051d4497b2d17f6cd5330330543a359e1dc6ed1c7f674ad4cac32`
- Packet-capture SHA-256: `8a57a70e9c36988dbb5579c3ca342856ab88ee3a2b92f88102da26fa90f70c37`

After cleanup, no run-owned process or listener remained. Gateway, DNS, HTTPS egress, and both redirect sysctls matched baseline.

## Boot identity correction

Ping plus stale neighbor-cache state falsely accepted `192.168.1.61` after the receiver moved to `192.168.1.62`. The exact-target scripts now require a direct ARP reply containing the receiver MAC. Historical addresses remain bounded candidates only; they are never spoofed or scanned as a range. The successful address is stored in `captures/receiver_last_ip` for the next launch.
