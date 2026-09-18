# Lab Experiment Log

## Experiment 001: USB Boot & Recovery Probe
- **Date:** 2026-09-17
- **Target Device:** Sagemcom DSI74 (STMicroelectronics STiH237)
- **Probe Media:** Removable USB Flash Drive (MBR, FAT32 labeled `MERO_STB`)
- **Payload Directory:** `probes/usb-001/`

### Drive Configuration Details
```text
Disklabel type: dos
Device     Boot Start      End  Sectors Size Id Type
/dev/sde1  *     2048 16076799 16074752 7.7G  c W95 FAT32 (LBA)
Filesystem: FAT32 (label: MERO_STB)
```

### Speculative Probes Deployed
- `README.TXT` (Human verification text)
- `update.bin` (0-byte candidate)
- `upgrade.bin` (0-byte candidate)
- `recovery.bin` (0-byte candidate)
- `firmware.bin` (0-byte candidate)

### Bench Test Protocol
1. **Safety Check:** Ensure SoC heatsink and thermal interface are secured before applying power.
2. **Connectivity:**
   - **Video:** Connect HDMI or CVBS to a display monitor to observe any recovery or splash screens.
   - **Network:** Connect RJ-45 Ethernet cable to observe DHCP/ARP requests or traffic on known subnet (e.g., historical host IP 192.168.1.134).
   - **Storage:** Insert USB drive into front/rear USB port while unit is powered off.
3. **Power-On & Observation:**
   - Cold-boot the STB.
   - Observe USB drive activity LED (does it stay off, illuminate steady, or exhibit burst reads?).
   - Observe front-panel LEDs / numeric display for status codes or reboot cycles.
   - Observe video output for bootloader or recovery prompts.
4. **Outcome Assessment:**
   - **Scenario A (Active USB Reads / Recovery UI):** Reverse engineer the expected recovery payload format.
   - **Scenario B (No USB Activity / Standard Boot):** Proceed to Phase 1 (dump SPI NOR boot flash).
