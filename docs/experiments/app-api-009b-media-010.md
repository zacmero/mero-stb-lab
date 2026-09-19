# APP-API-009B + MEDIA-010: Deep Runtime and Media Probe

## Purpose

This is one bounded hardware session that exhausts the remaining safe Ekioh application-runtime surfaces and tests the first local media path. It is bundled to avoid repeated cold boots and interception setup.

The application is `web/app-api.svg`. It records receiver-only evidence through `/app-api/report` into `captures/app-api-009b-media-010.json`.

## APP-API-009B probe matrix

- own-property or enumerable-property names for `window`, `document`, `navigator`, the SVG audio element, `ekiohPlatformInfo`, and its prototype;
- types of known network, storage, worker, database, OIPF, DVB, media, and USB globals;
- bounded `navigator.plugins` and `navigator.mimeTypes` inventories;
- named, read-only `ekiohPlatformInfo` candidates such as model, firmware/software version, and OS identity;
- document and location metadata;
- reversible `sessionStorage`, `localStorage`, and cookie round trips;
- one namespaced `localStorage` marker (`mero_probe_009b_persist`) retained so a later cold boot can establish whether origin storage persists;
- standard HTML audio/video creation and `canPlayType()` for WAV, MP3, Ogg, MP4, MPEG, MPEG-TS, and HLS MIME types.

Property discovery is not permission to invoke a discovered method. No shell, firmware, filesystem, tuner, USB, power, or privileged method is called.

## MEDIA-010 evidence levels

The host generates a quiet 440 Hz, 500 ms, mono PCM WAV at `/media/test.wav`; no binary fixture or Internet service is required.

The selectable `RUN LOCAL AUDIO TEST` action:

1. attempts the SVG 1.2 audio element's `beginElement()` only if present;
2. fetches the WAV with the demonstrated XHR path;
3. records the fetch status and received byte count.

Keep these observations distinct:

- `canPlayType()` is only advertised capability;
- an HTTP request proves resource retrieval;
- successful `beginElement()` invocation proves API availability;
- audible output proves playback;
- none of those alone proves hardware decoding.

## End Session behavior

The screen has two arrow-selectable actions. `UP`, `DOWN`, `LEFT`, or `RIGHT` changes selection and `OK` activates it.

`END SESSION AND CLEAN NETWORK` requests `/app-api/end-session`. The endpoint accepts it only from the exact receiver hardware. It writes a per-run signal inherited from `run_net_config_005.sh`; the runner notices within one second and enters its existing cleanup trap. Cleanup removes the signal, so it cannot end a later run.

This restores host interception state. It cannot close the injected top-level receiver document; APP-EXIT-008 established that a cold power cycle remains necessary.

## Testing the service classes left open by NETWORK-SERVICE-011

### Boot-time services

Start a MAC-filtered capture before applying power, record DHCP/ARP/DNS and every receiver flow with monotonic timestamps, and run only exact-target probes in short documented windows as boot phases change. Compare cold boot, normal runtime, and application launch. Retest narrowly any port observed only during a boot window. No subnet-wide ARP spoofing is needed.

### Receiver-initiated services

The receiver must create the first connection. Capture its DNS answers and outbound destination tuple, then emulate or intercept only that observed host, protocol, and path. Record the exact request before returning a minimal protocol-correct response. This is the proven model behind the HTTP application channel and is the most promising network route for update/configuration discovery.

### Internal or loopback-only services

These cannot be disproved from another LAN host. Evidence requires one of: a firmware/update image for offline filesystem and init-script analysis; a native execution or file-read foothold; a UART/console boot log; or a vendor diagnostic that relays the internal endpoint. Until one exists, internal services remain unknown rather than absent.

## Hardware procedure

1. Start the exact-target harness and wait for its post-interception health check.
2. Open Vivo Play once.
3. Wait until `API inventory: COMPLETE` appears.
4. With `RUN LOCAL AUDIO TEST` selected, press `OK` once and note whether a short quiet tone is audible.
5. Press `DOWN` once; confirm `END SESSION AND CLEAN NETWORK` is selected.
6. Press `OK` once. The host should report verified cleanup within one second.
7. Cold reboot the receiver to leave the injected document.

Do not press Vivo Play until the host explicitly reports that the harness is ready.

## Hardware result — 2026-09-19

The exact receiver at `192.168.1.57` / `68:15:90:6b:81:96` fetched `app-api.svg` at `04:55:42.727700Z`. The 13,583-byte document SHA-256 was `3a4cca89bcd0c66bf26deedd2b314a65d04b3dd814f3a9083e0f80d62d1d9f78`. The durable evidence contains 128 named observations; its SHA-256 is `b29562a0ab9c96c6249fe11d02d9e8b6774a71c8ee88ba502f86893e496773d0`.

### APP-API-009B

- `probe.complete=yes`; user agent `Ekioh v2.2.4.5-sagem (Mar 2 2013) r10767`, platform `SagemcomDFB`.
- `window` exposed 184 own properties. Newly important global names include `createConnection`, `createConnectionServer`, `createTimer`, `gotoLocation`, `binaryToString`, `stringToBinary`, `getURL`, `postURL`, `parseXML`, `setHTTPDigestCredentials`, `profiling`, `jsHeapUsed`, and `jsHeapMax`.
- Discovering those names does not establish their signatures, permissions, transport reach, or an OS-command bridge. Network/server and GC-related functions were not invoked blindly.
- `ekiohPlatformInfo` had no own properties, but its prototype exposed `POWERSTATE_STANDBY`, `POWERSTATE_ON`, and `suspendGC`. Guessed model, version, OS, and serial fields were undefined.
- One plugin/MIME entry existed: `application/mozilla-npruntime-scriptable-plugin`, described as `Scriptability Demo Plugin`. No plugin filename/name was exposed by the indexed plugin object.
- Local and session storage round trips passed; the cookie round trip passed. The persistent local-storage marker was absent before this first run and was written for a later cold-boot persistence check.
- HTML audio/video objects could be created, but `play`, `pause`, and `canPlayType` were undefined. The HTML object element had a string `data` field but no exposed `contentDocument`.
- DOM `hasFeature` and tested lifecycle/visibility properties were unavailable.

### MEDIA-010

The SVG audio object exposed `beginElement()` and `endElement()`. The receiver invoked `beginElement()` and fetched the complete 8,044-byte WAV repeatedly; the response SHA-256 began `007f573ed5be6bd0`. The user heard no tone and observed no post-action screen change.

Verdict: **POSITIVE for SVG media API presence and resource retrieval; NEGATIVE for audible playback of this PCM/WAV test.** This does not exclude other codecs, proprietary media elements, muted/mixed output paths, or hardware decoding.

### End Session and cleanup

Remote selection movement and `OK` were recorded. At `04:56:14.832375Z`, the verified receiver requested `/app-api/end-session` and received HTTP 200; a second request was harmless. The runner consumed the signal and terminated. All run-owned processes were gone, the receiver retained its correct IP/MAC mapping, gateway/DNS/HTTPS checks passed, and both `send_redirects` sysctls were restored to `1`.

The TV did not visibly acknowledge the action and remained in the injected document. This is consistent with APP-EXIT-008: **End Session is a successful host-network cleanup control, not a native receiver exit.**
