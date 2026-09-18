# STMicroelectronics STiH237 Platform Research

## Platform Architecture: "Cardiff"

The STiH237 belongs to STMicroelectronics' Cardiff family of integrated satellite decoder SoCs:
- **Application CPU:** ST40-300 core executing the SuperH SH-4 instruction set architecture.
- **Operating Frequency:** 450 MHz – 650 MHz.
- **Software Ecosystem:** Historically targeted by ST's proprietary STLinux 3.x distribution (specifically Linux kernel 3.4.58 with STAPI drivers for hardware video decode, DirectFB, and audio routing).

---

## Hardware Debugging Interfaces & Pinouts

### JTAG Interface
From STiH237 silicon ball-out documentation:

| Signal | BGA Ball Location | Description |
| :--- | :--- | :--- |
| **TDO** | `BF16` | JTAG Test Data Out |
| **TDI** | `BF17` | JTAG Test Data In |
| **TCK** | `BG16` | JTAG Test Clock |
| **TRST#** | `BG17` | JTAG Test Reset (Active Low) |
| **TMS** | `BG18` | JTAG Test Mode Select |

> **VOLTAGE WARNING:** On STiH237 designs, JTAG I/O banks typically operate at **1.8V logic levels**. Connecting 3.3V or 5.0V JTAG adapters (e.g., standard FT232H, Raspberry Pi GPIO, or Arduino) without bi-directional level shifters risks irreversible gate damage to the SoC.

### Serial Debug UART
STiH237 evaluation platforms and OEM bootloaders configure standard UART with:
- **Baud Rate:** `115200`
- **Data Bits:** `8`
- **Parity:** `None`
- **Stop Bits:** `1`
- **Flow Control:** `None`
- **Logic Voltage:** Typically 3.3V TTL (must be verified on test points prior to connection).

---

## Memory & Boot Subsystem Overview
- **Boot Sequence:** Internal BootROM on power-up -> evaluates boot configuration pins (boot straps) -> fetches first-stage bootloader from designated media (typically SPI NOR flash) -> initializes DDR3 controller -> hands over execution to second-stage bootloader (Das U-Boot) -> loads kernel from NAND flash into RAM.
- **Security Fuses:** Contains OTP (One-Time Programmable) eFuses capable of locking JTAG debug ports, enforcing cryptographic signature checks on the initial boot stage, and encrypting flash contents.
