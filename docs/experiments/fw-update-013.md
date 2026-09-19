# FW-UPDATE-013: Firmware and Update-Service Discovery

## Status

**IN PROGRESS — network relay capture aborted; offline discovery continues.**

No firmware manifest, package, installation path, signature policy, or rollback behavior has been identified.

## Existing receiver evidence

Committed captures contain receiver requests for configuration, highlights, portal redirect, and application assets. They contain no observed firmware manifest, package URL, or update request.

The receiver exposes these version strings:

- request firmware: `RC1.12.12`
- request software: `1.0.5`
- configuration version: `1.320.1.0.5`

These strings identify installed components. They do not identify an update package or prove that the receiver supports network updates.

## Aborted pass-through capture

At approximately 2026-09-19 19:32:04 -03:00, an experimental pass-through mode started an exact receiver↔gateway ARP relay and MAC-filtered packet capture. It did not redirect HTTP or HTTPS and did not serve any response.

Observed impact:

- the workstation's living-room SSH connection dropped briefly;
- another television on the LAN briefly disconnected;
- the test receiver made unanswered TCP SYN attempts to `191.32.31.251:80`, `191.32.31.251:443`, and `186.215.183.217:80`;
- the workstation NIC retained carrier; kernel logs show only entry to and exit from promiscuous mode.

The session was terminated at approximately 2026-09-19 19:36:38 -03:00. Cleanup verification established:

- no experiment runner, ARP redirector, interceptor, or packet capture process remained;
- zero `MNC005` firewall rules remained;
- `net.ipv4.conf.all.send_redirects = 1`;
- `net.ipv4.conf.enp5s0.send_redirects = 1`;
- gateway ping returned 4/4 replies at approximately 0.5 ms;
- DNS resolved `example.com`;
- HTTPS returned status 200.

The partial artifact remains at `captures/fw-update-013.pcap`. It contains no completed external TCP handshake and therefore no HTTP request, TLS ClientHello, update path, or package metadata.

### Interpretation

The host NIC did not disconnect. Because the SSH session and another television were both affected, router or switch reaction to ARP manipulation is the leading hypothesis. The available evidence does not identify the router's exact internal mechanism.

### Permanent correction

The uncommitted pass-through mode was removed. Do not use ARP relay capture for FW-UPDATE-013 again. The existing application interception harness was not changed by this aborted design.

## Offline service discovery

The observed hostname remains active:

```text
ucstb.vivoplay.com.br
  CNAME ucstb.br.gvp.telefonica.com
  A     213.140.61.225
```

The live HTTPS endpoint presents a valid `*.vivoplay.com.br` certificate and returns nginx HTTP 404 at `/`. Port 80 refused the tested connection. The exact previously observed `/tv-config/appConfigFit.json` path also returned 404 on the current hostname.

RDAP and reverse DNS attribute both historical IP ranges to Telefônica Brasil:

- `191.32.31.251.static.adsl.gvt.net.br`
- `186.215.183.217.static.host.gvt.net.br`

The Internet Archive index contains 413 successful archived URLs for `ucstb.vivoplay.com.br`. Filtering their paths for update-related terms found only `/service3.0/ConfigurationService.svc/GetInstanceSettings`. One archived response returned `StatusCode: 3`, `Content: null`, and no update URL. Archived authentication/configuration calls prove the host served Vivo Play APIs, not that it served receiver firmware.

## SoC security lead

The public repository `trojkowy/Glitching-STIH237-SOCs` is the only GitHub repository found by the `STiH237` identifier. Its author reports sentinel-guarded JTAG access, randomized clocks, encrypted secure boot with repeated signature verification, external-clock checks, and RAM scrambling.

That repository does not demonstrate a successful bypass. Its script requires ChipWhisperer and FT4232H-class hardware and invokes an STiH205/207 target pack. Treat its security description as an external report about the SoC family, not verified evidence for this DSI74 board or firmware.

The workstation exposes only one active Ethernet interface. A transparent two-port capture bridge is therefore not currently available without adding or reconfiguring network hardware. No bridge configuration was attempted.

## Safe continuation

Continue without LAN interception:

1. Search public archives, vendor material, and existing local artifacts for this exact model and version strings.
2. Analyze any obtained package offline with hashes, file-type detection, entropy, strings, archive extraction, filesystem identification, and signature metadata.
3. Extract init scripts, service definitions, Ekioh configuration, USB/update handlers, trust anchors, and maintenance listeners from an authentic image.
4. Resume USB work later with OS-level detection, updater UI behavior, media import, and USB HID. Do not infer those results from USB-CAP-012.
5. Do not offer any image to the receiver until package authenticity, model match, signature enforcement, rollback behavior, and recovery path are understood.
