# Boot Architecture & Strategy

## Core Philosophy: The USB Tether Strategy

Modifying the internal boot flash directly introduces high risk of unrecoverable bricking. The OEM bootloader is the most valuable piece of system software on the board because it has already solved:
- Clock generation and PLL setup for the STiH237.
- DDR memory timing calibration.
- Pin multiplexing and peripheral routing.

Our development strategy follows the **USB Tether Model**:

```
INTERNAL FLASH
┌─────────────────────────────────┐
│ Original Sagemcom Bootloader    │ (Remains untouched)
└───────────────┬─────────────────┘
                │ Interrogates / loads
                ▼
           USB STICK
┌─────────────────────────────────┐
│ Custom Linux Kernel (STLinux)   │
│ Custom Buildroot Rootfs         │
└───────────────┬─────────────────┘
                │ Boots into
                ▼
            RAM (256 MB)
```

### Safety Advantages
1. If the custom kernel crashes, panics, or corrupts userspace, removing the USB stick returns the device to its pristine factory state.
2. Development iteration involves updating files on the USB drive without wearing or stressing internal flash chips.

---

## Phase 0: Non-Invasive USB Probe (Current Phase)
Prior to extracting or altering flash:
1. Probe whether the OEM bootloader scans USB for update or recovery images on cold boot.
2. Probe filenames: `update.bin`, `upgrade.bin`, `recovery.bin`, `firmware.bin`.
3. If an activity LED flashes or boot behavior changes, investigate the OEM recovery protocol.

---

## Phase 1: SPI Boot Flash Extraction (Fallback)
If the OEM bootloader does not autonomously boot from USB or react to probe filenames:
1. Dump the SPI NOR flash chip using an external hardware programmer (e.g., CH341A / SOIC clip).
2. Binary inspection using string extraction:
   ```bash
   strings bootflash.bin | grep -Ei 'uboot|u-boot|usb|fat|ext2|bootcmd|bootargs|kernel|update|upgrade|recovery|nand|console'
   ```
3. Locate the U-Boot environment block (`bootcmd`, `bootargs`, console settings).
4. Patch `bootcmd` to attempt a USB boot first (`usb start; fatload usb 0:1 ...; bootm ...`) before falling back to internal NAND.
5. Write the patched image back to SPI flash.

---

## Phase 2: Target Software Stack (Mero-STB v0.1)

### Linux Kernel & BSP
- **Kernel Base:** Historical STLinux 3.4.58 BSP.
- **Justification:** STMicroelectronics explicitly validated Linux 3.4.58 against the STiH237 / Cardiff architecture (with 256 MB RAM configurations). This eliminates the friction of porting unsupported modern mainline kernels to closed proprietary 2013 multimedia SoC silicon.

### Userspace (Buildroot)
- **Target Architecture:** SuperH SH-4 (ST40).
- **Core Components:**
  - BusyBox (`sh`, standard coreutils).
  - DHCP Client.
  - Dropbear SSH server + `scp`.
  - `procps-ng`, `iproute2`.
  - USB Mass Storage driver support.
  - DirectFB / Framebuffer utilities for console display over HDMI/CVBS.

### Target Milestone
```bash
ssh root@mero-stb
```
Providing headless, stable network shell access over Ethernet, after which multimedia and display drivers can be methodically brought up.
