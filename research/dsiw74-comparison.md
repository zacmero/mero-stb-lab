# Sibling Platform Comparative Analysis: Sagemcom DSIW74

## Overview
The Sagemcom DSIW74 (marketed as "wifiBOX+" by Canal+ in Poland) is a close architectural sibling to the DSI74 V2 HD GVT. Prior reverse engineering work by satellite hardware communities provides important comparative data.

---

## Comparative Matrix

| Feature | Sagemcom DSIW74 (Poland) | Sagemcom DSI74 V2 (Brazil) |
| :--- | :--- | :--- |
| **SoC** | STMicroelectronics STiH237-SKB | STMicroelectronics STiH237 |
| **RAM** | 512 MB DDR3 | 256 MB / 512 MB DDR3 (Elpida J4216EFBG) |
| **Boot Flash** | 2 MB or 4 MB SPI NOR Flash | SPI NOR Flash (exact IC/designator under mapping) |
| **Main Storage** | 128 MB SLC NAND Flash | Micron BGA Flash (Marked "3QD17...") |
| **Wi-Fi** | Integrated USB-attached Ralink RT5572 | None internal (relies on external USB dongle) |
| **JTAG Status** | Hardware debug ports locked by OTP fuses | **Unconfirmed** on this board revision |
| **Console UART** | Often silenced or disabled in production firmware | **Unconfirmed** on this board revision |

---

## Key Lessons from Community Research

1. **JTAG Flash Lockout:** Enthusiasts attempting in-circuit JTAG on DSIW74 units found that while the TAP controller responds with the CPU IDCODE, memory bus access and flash programming were locked out by the SoC's security configuration.
2. **Flash Encrypted / Signed Payloads:** Dumps obtained from DSIW74 NAND partitions indicated operator-specific encryption or signing for second-stage payloads.
3. **Methodological Rule for DSI74 V2:** Do not assume that GVT/Vivo implemented identical fuse configurations or security locks as Canal+. The DSI74 V2 must be characterized on its own empirical merits.
