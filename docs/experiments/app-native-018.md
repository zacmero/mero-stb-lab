# APP-NATIVE-018: scriptable-plugin instantiation

## Result

**COMPLETED — LIMITED / NEGATIVE.** The receiver ran the controlled SVG script,
but the tested dynamic XHTML `<embed>` construction did not instantiate the
advertised `application/mozilla-npruntime-scriptable-plugin` native object. It
remained an ordinary SVG DOM element. This closes the direct `<embed>` route as
tested; it does not establish that every proprietary plugin-loading path is
absent.

## Scope and safety

The experiment used the direct-cable isolated lab and only receiver-initiated
HTTP. It redirected the known `/bussola/redirect` request to a local document,
then accepted telemetry at `/app-native-018/report`. It did not call an unknown
plugin method, alter receiver storage, scan the receiver, relay LAN traffic, or
expose a listener outside the direct cable. IPv4 forwarding stayed disabled.

## Tested documents

| Variant | Delivery | Observed result | Classification |
| --- | --- | --- | --- |
| A | Top-level HTML with object/embed markup | The document fetched; no telemetry callback arrived. | Negative for that document form. |
| B | Top-level XHTML with object/embed markup | The document fetched; no telemetry callback arrived. | Negative for that document form. |
| C | Static SVG embedding forms | The document fetched; no telemetry callback arrived. | Negative / parser-sensitive. |
| D | SVG root `onload` dynamically adding an embed | The document fetched; root `onload` did not run. | **Invalid control**, not plugin evidence. |
| E | Parse-time SVG script, proven `getURL()` control, delayed dynamic XHTML `<embed>` | Script and reflection telemetry arrived. | Valid negative for the tested instantiation route. |

## Verified E transaction

At `2026-09-20T02:50:23Z`, the receiver (`10.74.0.10`) requested
`/bussola/redirect` and received `302 Location: /app-native-018e.svg`. It then
fetched the 2,325-byte SVG, SHA-256
`81c17938e699998284281f6536afc8f07fb313de5659c58ebc5bb1fffcdbf31f`.

The document immediately sent `control.loaded=true`, then created a single
XHTML `embed` after 500 ms with MIME type
`application/mozilla-npruntime-scriptable-plugin`. The receiver reported all
of the following at `2026-09-20T02:50:24Z`:

- `embed.start=true` and `embed.appended=true`;
- `typeof embed === "object"`;
- `String(embed) === "[object SVGElement]"`;
- ordinary DOM property surfaces, including `data` and event methods;
- `embed.object === "undefined:undefined"`;
- `embed.complete=true`.

The normal configuration request followed at `2026-09-20T02:50:40Z`. The raw
capture is retained on the isolated laptop under
`captures/20260920T024909Z/http.jsonl` and `receiver.pcap`; those data are not
committed because they include receiver-identifying request material.

## Interpretation

The `getURL()` control proves that the E script executed and that its reports
traversed the receiver's actual network stack. Therefore the absence of a
plugin object is not explained by a general script failure or missing callback
path. The evidence supports one narrow conclusion: this SVG runtime treated
the dynamically created XHTML `<embed>` as SVG DOM, rather than loading an
NPAPI-like native object.

No native method was invoked. This experiment provides no evidence of shell
execution, arbitrary native code, filesystem access, USB access, a persistent
service, or an OS bridge.

## Harness lifecycle

The added `native018` through `native018e` profiles are explicit, asset-checked
routes in `scripts/run_isolated_receiver_lab.sh` and
`scripts/isolated_http_logger.py`. `scripts/test_isolated_http_logger.py`
checks every redirect and asset response. The lab runner's signal trap stops
the HTTP logger, `dnsmasq`, and `tcpdump`; removes its three Ethernet addresses;
restores NetworkManager management; and retains forwarding at its original
value. It never changes Wi-Fi routing or household-router state.

## Follow-up boundary

Do not expand native-plugin probing by blind method enumeration. The useful
next software route is firmware/update-chain analysis using authentic artifacts
or a read-only flash dump. Application work remains useful for dashboards,
control surfaces, and receiver-authorized network clients, but it is not an OS
execution route on current evidence.
