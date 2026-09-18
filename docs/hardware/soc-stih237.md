# Core SoC: STMicroelectronics STiH237 ("Cardiff")

## Silicon Identification

Physical inspection under the primary heat-spreader confirms:

```text
STMicroelectronics
STiH237
Cardiff family
```

## Architecture & Features

The STiH237 is an integrated high-definition satellite set-top box SoC based on ST's ST40 application CPU architecture:

- **CPU Core:** ST40-300 core (SuperH SH-4 family architecture), typically clocked between 450 MHz and 650 MHz.
- **Memory Subsystem:** High-speed DDR2/DDR3 memory controller.
- **Boot & Storage Controller:** Interfaces for SPI serial NOR flash and parallel/serial NAND flash.
- **Networking:** Integrated 10/100 Mbps Ethernet MAC.
- **USB:** Integrated USB 2.0 Host controller (EHCI/OHCI).
- **Video Processing:** Hardware multi-standard video decoding engine (MPEG-2, H.264/AVC HP@L4.1, VC-1), hardware graphics acceleration, HDMI 1.3/1.4 Tx with HDCP, and multi-format analog video DACs (CVBS, YPbPr).
- **Security Subsystem:** On-chip secure boot engine, hardware cryptographic accelerators (AES, DES, 3DES), and one-time programmable (OTP) fuses for chip-level pairing and secure lifecycle states.

## Thermal Management Requirement

> **CRITICAL WARNING:** The STiH237 dissipates substantial thermal energy during active execution. The original aluminum heat-spreader/shield makes direct contact with the SoC package via an elastic thermal interface material.
>
> **The heatsink MUST be re-seated before any prolonged powered operation.** Operating the board uncooled risks silicon degradation, thermal throttling, or permanent latch-up.
