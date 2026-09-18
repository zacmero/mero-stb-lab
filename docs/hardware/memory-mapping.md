# Memory & Storage Components Classification

This document records confirmed component markings from high-resolution PCB photographs and schematic cross-references.

---

## 1. System RAM: Elpida J4216EFBG

- **Package:** FBGA, high-density length-matched trace routing directly to STiH237.
- **Marking:**
  ```text
  ELPIDA
  J4216EFBG...
  ```
- **Classification:** **System DRAM (DDR3 SDRAM)**.
- **Datasheet Correlation:** The `EDJ4216EFBG` / `J4216EFBG` series represents a 4Gb (256M x 16 or 512 MB) / 2Gb (256 MB) DDR3 SDRAM device.
- **Role:** Volatile main system memory. **Not nonvolatile firmware storage.**

---

## 2. Storage Flash (NAND): Micron BGA (Marking "3QD17...")

- **Package:** BGA adjacent to the SoC core.
- **Marking:**
  ```text
  Micron Technology
  3QD17 ...
  ```
- **Classification:** **Nonvolatile Storage (Likely SLC NAND Flash)**.
- **Status:** **Unresolved capacity / full part number.**
- **Notes:** Micron uses 5-character FBGA codes (e.g. `NWxxx`, `JZxxx`, `D9xxx`) on small BGA packages. "3QD17" represents an abbreviated lot/FBGA marking that requires verification via the Micron FBGA decoder against SLC NAND part families (e.g., `MT29F1G...` 128 MB SLC NAND, which is standard on Sagemcom DSIW74/DSI74 hardware).
- **Role:** Holds the large vendor system partitions, kernel images, and operator root filesystems.

---

## 3. Front Panel Controller: Princeton Tech PT6958

- **Package:** 28-pin SOP (TSOP-like form factor).
- **Marking:**
  ```text
  PT6958
  TSK06T
  1HB421
  ```
- **Classification:** **Display Controller & Key-Scan Peripheral IC**.
- **Datasheet Specifications:**
  - Manufacturer: Princeton Technology Corp (PTC).
  - Function: 1/6 duty factor LED driver with 10 segment outputs and 5 grid outputs.
  - Key scanning: 6 x 4 matrix keyboard scanner.
  - Interface: 3-line serial communication (CLK, STB, DIN/DOUT) communicating with the main SoC.
- **Architectural Fact:** **This is NOT nonvolatile firmware storage.** It handles the front-panel 7-segment display and pushbuttons.

---

## 4. Boot Flash (SPI NOR): MX25L1606E (Hypothesis Under Verification)

- **Status:** **Tentative / Unconfirmed on PCB.**
- **Hypothesis:** Prior discussions suggested an `MX25L1606E` (16 Mbit / 2 MB) or 32 Mbit (4 MB) serial SPI NOR flash in 8-pin SOP/SOIC.
- **Rule:** Do not treat this identification as confirmed until the physical reference designator (e.g., `Uxx` or `ICxx`), pin connections, and package markings on the M74X-1 PCB photograph are directly mapped and verified against the M74-1 schematic.
