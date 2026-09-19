# RUNTIME-PROBE-009G: Combined Runtime Behavior Probe

## Status

**COMPLETED — POSITIVE** on 2026-09-19.

This automatic application combines several bounded runtime questions into one receiver launch:

1. Create one native timer with a 150 ms delay, attach `timer`, `timeout`, and `tick` listeners, start it, observe state for 1.2 seconds, stop it, and record event counts.
2. Test three fixed two-argument `stringToBinary` forms and matching `binaryToString` forms using only `MERO-009G`.
3. Dispatch one in-document custom event and mutate one in-memory XML document.
4. Verify JSON, local/session storage, a three-tick standard interval, and heap readings.

Results use the proven sequential one-request-at-a-time queue. The application runs every phase automatically and requests harness cleanup only after the final result is delivered. No remote navigation is required.

The probe does not request filesystem, process, USB, firmware, power-state, tuner, or unrestricted network operations.

## Hardware result

The verified receiver at `192.168.1.62` completed all four phases and delivered 50 result fields before requesting cleanup.

### Native timer

`createTimer(150, 0)` returned an object with `delay`, `repeatInterval`, `running`, `start`, and `stop`.

- Before `start()`: `delay=150`, `repeatInterval=0`, `running=false`.
- Immediately after `start()`: `running=true`.
- After 1.2 seconds: `running=false`.
- After `stop()`: `running=false`.
- `start()` and `stop()` each returned their native function representation.
- Listeners for `timer`, `timeout`, and `tick` attached successfully, but none fired.

The state transition demonstrates that the native timer ran and completed. Its actual event name remains unknown.

### Data helpers

Both `stringToBinary` and `binaryToString` have arity 2. The `UTF-8` form succeeded:

```text
stringToBinary("MERO-009G", "UTF-8") -> binary object
binaryToString(binary, "UTF-8") -> "MERO-009G"
```

Numeric second arguments `0` and `10` raised `[object GlobalException]`.

### DOM, XML, storage, and timing

- A custom DOM event dispatched once and its listener ran once.
- `parseXML()` returned an object without `createElementNS`; the attempted document-style mutation raised `TypeError: parsed.createElementNS is not a function`.
- JSON encode/decode preserved the marker.
- Local and session storage round trips succeeded.
- A standard interval fired exactly three times and was cancelled.
- JavaScript heap use increased from 147,456 to 151,552 bytes during the bounded probe.

### Evidence and cleanup

- Application SHA-256: `745a0d5010fe32d1ddecba8db2e9059ef71b727a5bf6a6cc705255f6e34d44f3`
- Result SHA-256: `6c8891e294b173893aaafc99eb908a4cacef96f03db9ff3c5229355758b93bb5`
- Packet-capture SHA-256: `d3827aac1ff9bc3b26eaf17e1ee14d35bb409e3aae0e470dec1e63a16a6936f4`

`automatic.result=complete` was delivered at `2026-09-19T21:23:11.373553Z`. Cleanup removed all run-owned processes, listeners, and firewall rules. Gateway, DNS, HTTPS egress, and redirect sysctls matched baseline.
