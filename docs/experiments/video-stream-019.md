# VIDEO-STREAM-019: router-connected video library

Status: SVG app and two direct-media responses delivered; no video playback observed.

The intended path is `/home/zacmero/Videos` on the bedroom PC, through the household router to the GVT receiver and HDMI TV. The disposable laptop is not part of playback. The app lists supported files and requests byte ranges; the TV must establish whether the receiver actually decodes video and audio.

## Corrected network finding

On 2026-09-24, the receiver still reported `192.168.1.61` with MAC `68:15:90:6b:81:96`. A reboot capture recorded it ARPing for gateway `192.168.1.1`. The attempted direct-PC-gateway session received no receiver HTTP requests and Vivo Play displayed a connection error. The receiver configuration screen does not expose the gateway change that the initial procedure assumed. That procedure and its runner were removed. The attempt did not test media decoding.

The replacement uses the previously demonstrated exact-receiver router harness (`scripts/run_net_config_005.sh`). It intercepts only traffic from the verified receiver IP/MAC, checks host gateway/DNS/HTTPS before and immediately after activation, and restores its exact ARP pair, owned firewall rules, and sysctls on exit. This remains a temporary test harness, not a permanent streamer.

## Implementation and host verification

- `web/video019.svg` loads the local library, starts its first video, and permits arrow/OK selection. It reports app and media events to `/video019/report`.
- `scripts/video_library_server.py` indexes supported files under `/home/zacmero/Videos`, rejects paths resolving outside that root, and serves HTTP ranges. Its handler is reused by the existing interceptor for `/video019/list` and `/video019/media/<id>`; no separate video-server process is needed on the router path.
- With `MERO_LAUNCH_APP=video019`, the proven `/portal.svg` entry chain sends `/launch.svg` to `/video019.svg`. Normal harness behavior is unchanged without that variable.
- Local HTTP checks returned `302` for `/launch.svg`, `200` for the SVG, `200` for the library list, and `206` for a 32-byte ranged media request. Unit tests, Python compilation, shell syntax, SVG parsing, and diff whitespace checks passed. These checks do not establish GVT playback.
- Two 12-second test clips exist in `/home/zacmero/Videos`: MPEG-2/MP2 transport stream and H.264/AAC MP4.

## Receiver observation on 2026-09-24

The exact receiver fetched `/bussola/redirect`, `/portal.svg`, `/launch.svg`, and `/video019.svg`. Its app reported `library.count=2`, selected both the MPEG-2 transport stream and H.264 MP4 with remote DOWN/OK, and invoked the SVG media element's `beginElement()`. The TV showed app text but no video. No receiver request to `/video019/media/<id>` occurred for either clip, including when the first clip URL was embedded as a static SVG `<video>` attribute. Thus codec compatibility remains untested; the failure is before a media-byte fetch. The engine also sent corrupt text values after repeated SVG text-node mutations, and a single DOWN press appeared to produce multiple selection changes. Do not infer a decoder failure from this session.

The direct-media test uses `MERO_LAUNCH_APP=video019_direct`: the existing `/launch.svg` redirect points straight at the first library video with `video/mp2t`, bypassing the SVG media element. A local HTTP check followed that redirect and received a 206 range response before the receiver test.

### Direct-media result

At `2026-09-24T14:23:32Z`, verified `RECEIVER_HW` fetched `/launch.svg`, followed its 302 to `/video019/media/dd9482c575827180`, and received HTTP 200 `video/mp2t`. The TCP capture for receiver source port `42937` shows the receiver acknowledged byte sequence `3121555`: initial response sequence `1` + 190 response-header bytes + 3,121,364 file bytes. The full MPEG-2/MP2 transport-stream response therefore reached the receiver. The user observed only the Vivo Play “Please wait” screen for almost a minute, with no video. This is a negative top-level playback result, **not** a network-delivery failure. It does not establish whether the same runtime could play another container or codec through a different native playback API. The harness was terminated; no owned processes remained, and gateway, DNS, HTTPS, and the gateway's real MAC were verified after cleanup.

### MP4 direct-media result

At `2026-09-24T14:31:41Z`, the exact receiver fetched the H.264/AAC MP4 selected by `MERO_VIDEO_PREFERRED_EXT=.mp4` through the same top-level route. The TCP capture for receiver source port `34536` shows the receiver acknowledged sequence `2413991`: initial response sequence `1` + 189 response-header bytes + 2,413,801 file bytes. The full MP4 response reached the receiver, but the user again observed only “Please wait, loading.” Interception was stopped; no test processes remained and host gateway, DNS, and HTTPS checks passed. Both direct-container tests therefore demonstrate HTTP delivery without foreground playback. They do not prove either codec unsupported by the receiver's native TV/media stack; this SVG/browser launch path may not hand a top-level video response to that stack.

Further live video trials should wait for a more specific playback entry point (documented media API, native middleware contract, or an existing receiver media request) rather than repeat format swaps or require another reboot for an arbitrary file.

## Cleanup incident and correction

A post-session audit found stale `MNC005F_105058` and `MNC005N_105058` chains from the first VIDEO-019 run interrupted through the terminal wrapper. Both `send_redirects` sysctls were also still `0` even though ordinary connectivity checks passed. Later runs' chains had been removed. The exact stale FORWARD and PREROUTING links and their two run-owned chains were deleted; no unrelated firewall rules were flushed. Both sysctls were restored to their recorded original value `1`. A root recheck found no `MNC005` chains in filter or NAT, both sysctls at `1`, no test processes, and passing gateway, DNS, and HTTPS checks.

The runner now invokes cleanup directly on INT and TERM, verifies the restored sysctl values, and refuses a new run if any `MNC005` rule is already present. Shell syntax and local tests pass. The revised interrupt behavior has **not** been proven by another live interruption test; do not claim that an arbitrary process kill is safe. Before every future live run, inspect existing rules and host health, and after every run verify chains, sysctls, processes, and connectivity separately.

## Receiver test

Before opening Vivo Play, establish the receiver's current exact IP/MAC mapping; do not reuse `.61` if it changed. Start the existing root harness with `MERO_LAUNCH_APP=video019` and `RECEIVER_IP=<verified IP>`. Wait for its post-interception gateway/DNS/HTTPS check and `READY FOR CASE-00`. If a check fails, stop and inspect cleanup before another attempt. Do not broaden ARP targets or scan a range.

After `READY`, open Vivo Play once. Record exact `RECEIVER_HW` requests for `/bussola/redirect`, `/portal.svg`, `/launch.svg`, `/video019.svg`, `/video019/list`, and `/video019/media/<id>`, plus report callbacks. Observe the TV directly for motion and sound; successful HTTP delivery alone does not prove decoding. Stop the harness after the bounded test and verify gateway/DNS/HTTPS, ARP restoration, owned processes, and firewall chains. If the app remains foreground, a cold reboot may be needed to exit the receiver application.

If native video works, next measure playback smoothness and stability before considering a persistent, safer route. If it fails, use the request/report timeline to distinguish launch, SVG runtime, video fetch, and codec failures.
