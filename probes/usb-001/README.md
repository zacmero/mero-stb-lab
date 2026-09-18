# USB Probe 001: Bootloader Interrogation

## Objective
Non-destructive interrogation of the Sagemcom DSI74 onboard bootloader (STMicroelectronics STiH237 / Cardiff architecture).

The goal is to determine if the OEM first-stage bootloader executes an automatic recovery or firmware update scan on attached USB mass storage devices prior to booting the resident firmware from internal flash.

## Filesystem & Layout Configuration
- **Partition Table:** MBR / DOS partition table.
- **Partition 1:** Primary partition, type `0x0c` (`W95 FAT32 (LBA)`), flagged bootable (`*`).
- **Filesystem:** FAT32, formatted with volume label `MERO_STB`.
- **Block Allocation:** Starts at sector 2048 (1 MiB alignment) to partition boundary.

## Probe Payload Contents
The files in this directory represent the exact file layout deployed to the root of the probe drive:

| File | Size | Role |
| :--- | :--- | :--- |
| `README.TXT` | 58 B | Plaintext identification tag for humans and mount verification. |
| `update.bin` | 0 B | Speculative OEM recovery / update filename candidate. |
| `upgrade.bin` | 0 B | Speculative OEM recovery / update filename candidate. |
| `recovery.bin`| 0 B | Speculative OEM recovery / update filename candidate. |
| `firmware.bin`| 0 B | Speculative OEM recovery / update filename candidate. |

> **Important:** The `.bin` files are zero-byte filename probes, not valid executable firmware or bootloader binaries. They are designed solely to test whether the resident bootloader polls for these filenames on USB enumeration.
