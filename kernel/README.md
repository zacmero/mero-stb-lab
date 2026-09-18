# Kernel & BSP Strategy: STiH237 Cardiff

## Core Kernel Strategy: Historical STLinux 3.4.58 BSP

For the STMicroelectronics STiH237 ("Cardiff") platform, our strategy prioritizes reconstructing the **historical STLinux 3.4.58 BSP** over attempting to force a modern generic mainline kernel.

---

## Technical Rationale

1. **Proprietary SoC IP:** The STiH237 integrates proprietary clock trees, complex pin multiplexing, custom interrupt controllers, and specialized hardware decoders that were never upstreamed into the mainline Linux kernel tree.
2. **Proven Hardware Validation:** STMicroelectronics explicitly validated and supported STLinux 3.x (kernel 3.4.58) on Cardiff/STiH237 with 256 MB RAM configurations (including Media Player and IP profile builds).
3. **Shortest Path to Code Execution:** Leveraging known-working board support code, memory maps, and device tree/platform data drastically accelerates the path to a booting kernel with working Ethernet and USB.

---

## Target Output Format
- **Image Type:** `uImage` (U-Boot legacy image with standard ST40 load address).
- **Console Parameter:** `console=ttyAS0,115200` (or `ttySC0` depending on ST40 serial driver naming).
- **Root Parameter:** Configured to boot from RAM disk (`initrd`) or USB flash partition (`root=/dev/sda1 rootwait`).
