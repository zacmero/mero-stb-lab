# Sagemcom DSIW74 comparison — evidence-qualified reference

Updated **2026-10-26**. This compares a related-model research lead with Zac's DSI74 V2 GVT; it is not a local hardware-test result.

## Original source

[Guest romeok01 — SAGEMCOM DSIW74 - zdjęcia - analiza, 21–22 January 2015](https://forum.graterlia.tv/topic/885-sagemcom-dsiw74-zdj%C4%99cia-analiza/)

Read the [source audit and applicability notes](uart-reference-audit-2026-10-26.md) for the narrowly reported UART and JTAG outcomes, author/date, photo links and current owner priorities. This exact link was missing from the prior version of this file.

## What may and may not transfer

The shared processor-family lead makes the external investigation worth retaining. It does not establish identical PCB routing, boot configuration, firmware policy, security state or console availability on the GVT receiver.

Use the local [hardware overview](../docs/hardware/overview.md), [memory-mapping notes](../docs/hardware/memory-mapping.md) and actual experiment logs as evidence for our unit. In particular:

- The suspected SPI boot-flash identification remains a hypothesis pending physical confirmation; do not select firmware or a clip connection from it.
- UART pins, levels and functionality remain unmeasured in our receiver's new hardware session. Another unit's unsuccessful capture is not our failure result.
- JTAG permissions, fuses and firmware encryption/signatures are not locally verified. The source audit must not be expanded into claims of confirmed encryption or permanently disabled interfaces.
- Ekioh application execution is not an operating-system shell. Further UI experiments are not the owner's requested next milestone.

## Prior comparison retained in history

The [previous version](https://github.com/zacmero/mero-stb-lab/blob/6b5ca42d45965cc742adbe8ae7c7dba94b638ef4/research/dsiw74-comparison.md) contained an unsourced specification table and broader lock/encryption assertions. Preserve it as historical research, not established fact. This update replaces those assertions with traceable source scope rather than treating them as measurements of our board.

No device operation, firmware write, UART attempt or JTAG connection was performed by this documentation update.
