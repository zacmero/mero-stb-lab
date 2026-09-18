# Experiment Report: USB-PROBE-001

## Metadata
- **Identifier:** `USB-PROBE-001`
- **Date:** 2026-09-17
- **Target Hardware:** Sagemcom DSI74 V2 HD GVT - BRA (STMicroelectronics STiH237)
- **Status:** **COMPLETED**
- **Outcome:** **NEGATIVE**

---

## Executive Summary

```text
USB-PROBE-001
RESULT: NEGATIVE for demonstrated recovery/update triggering.

The receiver powers/accesses the FAT32 USB stick, but the observed
vendor "updating firmware" boot screen also occurs without the USB.
Therefore no USB recovery filename or arbitrary firmware-loading path
has yet been demonstrated.
```

---

## Test Media Configuration

A dedicated removable USB flash drive was prepared:
- **Partition Table:** MBR / DOS
- **Partition Layout:** Single primary partition spanning the full capacity, bootable (`*`), type `0x0c` (`W95 FAT32 (LBA)`).
- **Filesystem:** FAT32, volume label `MERO_STB`.
- **Root Directory Files:**
  - `README.TXT` (58 bytes, human banner)
  - `update.bin` (0 bytes)
  - `upgrade.bin` (0 bytes)
  - `recovery.bin` (0 bytes)
  - `firmware.bin` (0 bytes)

---

## Observations & Control Test

1. **USB Port Power:** Upon cold-boot with the USB drive inserted, the drive's power/activity LED illuminated.
   - *Technical Distinction:* An illuminated LED proves at minimum that the USB host port supplies 5V VBUS power to the device. Unless rhythmic read/write flash patterns are observed, an illuminated LED does not by itself prove that the bootloader mounted the filesystem or inspected the partition.
2. **Boot Screen Observation:** During cold-boot, the television screen displayed a vendor graphic indicating "updating firmware", followed by standard boot into the factory GVT application.
3. **Negative Control Execution:** The box was cold-booted **WITHOUT any USB stick connected**. The exact same "updating firmware" sequence displayed identically.

---

## Strategic Conclusion & Next Steps

The observed boot behavior is hardcoded into the vendor's standard initialization sequence and is completely unrelated to our USB probe files. 

- **Action:** Cease blind filename guessing. Random recovery filename probing without binary evidence is an inefficient path.
- **Pivot:** Transition immediately to **BOOT-CHAIN-001**: physical boot-chain archaeology, PCB-to-schematic mapping, identification of earliest external nonvolatile boot storage, and hardware debug interface analysis.
