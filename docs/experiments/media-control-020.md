# MEDIA-CONTROL-020: find the native playback bridge

Status: receiver probe completed; media element allocated but did not start playback.

VIDEO-STREAM-019 proved that the receiver's TCP stack acknowledged complete MPEG-2 and MP4 responses, but Vivo Play stayed on “Please wait.” The SVG `<video>` element did not even request bytes. A smooth, audio-synced stream needs access to the receiver's native media pipeline; frame-swapping is not the target.

Receiver evidence from `captures/app-api-009b-media-010.json` lists `EkiohMediaControl`, `EkiohStreamInfo`, `EkiohAudioStreamInfo`, and `EkiohSubtitleStreamInfo` in the runtime's global property names. Earlier probes did not enumerate the media-control constructor or its prototype. These names are a lead, not proof of an invocable player.

`web/media-control-020.js` is a hot-loadable module for the proven app hub. The first module version only reflected API names. Later versions created SVG video elements and attempted a bounded MP4 source load without rebooting. The hub manifest now has `cleanup: true` so an accidental relaunch ends host interception; set it to `false` only when a new bounded module is ready. The receiver may still need a cold boot to leave its foreground app.

## Receiver evidence

- The TV showed the runtime hub's initial text, apparently stuck at “version: none,” but receiver logs proved the manifest and module loaded. Static-looking UI text is not evidence that its script stopped.
- `EkiohMediaControl` is an object with prototype property names `audioStreams`, `videoStreams`, `audioStream`, `videoStream`, and `displayTeletext`; these returned `undefined` in the probed context. `SVGVisualMediaElement` exposes `position`, `currentTime`, `duration`, `playbackRate`, `ekiohControl`, and a callable `setSpeed` method.
- An attached SVG `<video>` without a source had `ekiohControl=undefined`. Adding an explicit `video/mp4` type and direct-LAN URL produced a visible black rectangle and `ekiohControl` object. That object's own-property list was empty and its inherited media-control fields still returned `undefined`. `currentTime` stayed `-1` after ten seconds. The direct-LAN server saw no receiver connection.
- A separate same-origin SVG media URL also produced no GET request, even after `beginElement()` returned and five seconds elapsed; `currentTime` stayed `-1`. Thus the media element/control object existed, but it did not begin loading either source. The black rectangle was not video playback.
- The hub's `cleanup: true` manifest caused a verified `RECEIVER_HW` end-session request. After cleanup, no `MNC005` filter/NAT chains or owned processes remained; both `send_redirects` sysctls were `1`; gateway, DNS, HTTPS, and the gateway's real MAC were verified.

The next decision is to identify a real native playback contract or firmware/client asset rather than retrying arbitrary codecs. The exposed names do not yet provide a callable player. The receiver may still have a native TV decode pipeline inaccessible through this browser context.

## Offline native-player research (2026-09-24)

The device's own runtime is the strongest source: `EkiohMediaControl` and `SVGVisualMediaElement` are present, but the probed stream fields are `undefined`, the SVG media clock stayed at `-1`, and neither a direct-LAN nor same-origin video source produced a media GET. Complete MPEG-2 and MP4 file delivery through a top-level redirect also did not start playback. These observations establish no working browser-to-player call; they do **not** establish that the silicon lacks a decoder or that all native firmware media paths are absent.

Ekioh's [2008 description of an IPTV deployment](https://www.ekioh.com/news/ekioh-ui-engine-integral-part-latest-freewire-iptv-stb-service/) identifies its SVG engine as a user-interface component used alongside Zignal middleware. Its [2018 description of an IP-video product integration](https://www.ekioh.com/news/exterity-selects-ekiohs-tv-browser-for-its-range-of-ip-video-products/) likewise places the browser beside the product maker's specialist components. This supports the architectural hypothesis that UI rendering and actual playback may be separate on embedded TV products. Neither article identifies this DSI74 firmware or documents an `EkiohMediaControl` invocation, so it cannot prove the hypothesis for our unit.

The repository has no usable receiver firmware image to inspect: `probes/usb-001/firmware.bin` is empty, and [FW-UPDATE-013](fw-update-013.md) records that no compatible update package or manifest has been identified. A bounded public-source search found no target-specific media-player API contract. The fastest next *offline* discriminator is therefore a genuine DSI74 firmware/client package or a read-only storage dump: inspect its binaries and configuration for the middleware/player process, IPC interface, media URL schemes, and the implementation of `EkiohMediaControl`. Do not substitute another model's firmware or infer an API from a name alone.
