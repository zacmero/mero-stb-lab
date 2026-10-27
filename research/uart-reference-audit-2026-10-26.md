# GVT receiver — original UART/JTAG reference and current limits

Recorded **2026-10-26 (America/Sao_Paulo)**. This is a source/documentation update, not a new receiver experiment.

## Original attempted-access report — recovered and checked

**Guest romeok01, “SAGEMCOM DSIW74 - zdjęcia - analiza”, Forum Graterlia, 21–22 January 2015:**

https://forum.graterlia.tv/topic/885-sagemcom-dsiw74-zdj%C4%99cia-analiza/

The first post describes three underside pads near SCART as suspected TX/RX/GND, reports 3.3 V, and says the terminal displayed nothing after connection. The follow-up on 22 January reports processor ID `1D44A041` through EJTAG CPLD TT, but blocked NOR/NAND memory access. The text identifies an STiH237 SKB and Spansion memories. It includes links to board photographs hosted on the old forum.xunil.pl service.

**This is an unsuccessful access attempt on a DSIW74, not a successful shell-unlock recipe and not a measurement of Zac's DSI74 V2 GVT.** The original UART statement is limited to the author's setup; it does not establish the reason for silence or prove every UART configuration fails. The later JTAG claim must likewise remain attributed to that unit/tool setup.

## Corrections to inherited research

[The older comparison](dsiw74-comparison.md) had no concrete source URL and used broader language about disabled UART, security fuses and encrypted/signed dumps. The recovered thread supports the narrower report above; it does **not** establish those broader claims on our receiver. Do not infer verified OTP settings, firmware encryption, pin voltage, boot order or a compatible image from it.

The existing [BOOT-CHAIN-001 plan](../docs/boot-chain/boot-chain-001.md) is a plan/hypothesis, not a completed physical measurement. Its “zero risk” characterization and its inference that serial silence proves a disabled console are too strong. A mistaken voltage, pin, contact or setup can invalidate a test. Do not execute that plan's boot/flash branches as automatically authorized operations.

## Our receiver's evidence and owner decision

The [local hardware inventory](../docs/hardware/overview.md), [memory classification](../docs/hardware/memory-mapping.md) and earlier [network/application reports](../experiments/net-config-005.md) preserve our own device work. Custom Vivo Play/Ekioh application execution was achieved; an OS shell was not demonstrated by that result. The owner now explicitly wants **shell/native-code access**, not more UI polishing, and reports that the UI/network experience is unsatisfactory.

No new GVT UART capture, programmer connection, flash read or modification was performed in the 26 October discussion. The suspected SPI boot-memory part/location is still unverified; the existing NAND lead is not something a SOIC8 clip can simply attach to. Similar-looking boards and eight-legged components are insufficient grounds to select a chip.

The received CH341A has an independently documented approximately 5 V signal problem, and the owner lacks individual jumper leads and soldering equipment. See the [MitraStar hardware record](https://github.com/zacmero/mero-mitrastar/blob/master/docs/experiments/mitra-hardware-020.md). Neither its USB enumeration nor the clip's existence provides a safe GVT wiring method.

## Next useful GVT work, when resumed

Prioritize evidence that can actually lead toward a shell: a matching firmware/update package for offline analysis, or an accurately identified electrical interface with suitable equipment. Do not promise a software escape from Ekioh or force a speculative hardware connection. Preserve earlier unsuccessful USB/network tests rather than repeating them without new evidence.

The owner's immediate active target is now the [Askey RTV9015VW handoff](https://github.com/zacmero/mero-askey/blob/main/HANDOFF.md), using Ethernet on Mint. This reference remains available for a later GVT session; no GVT firmware or service state was changed here.
