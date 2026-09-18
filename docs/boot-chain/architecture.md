# Target Boot Chain Architecture & Hypothesis

## Boot Chain Sequence Hypothesis

The execution sequence of the Sagemcom DSI74 V2 HD platform follows a multi-stage boot process typical of STiH237 designs:

```text
+-------------------------------------------------------+
| 1. Power Applied & Hardware Reset Released           |
+-------------------------------------------------------+
                           |
                           v
+-------------------------------------------------------+
| 2. On-Chip BootROM Execution (STiH237 Internal ROM)   |
|    - Initializes internal SRAM                        |
|    - Evaluates boot mode strap resistors / pins       |
|    - Checks security state / OTP fuses                |
+-------------------------------------------------------+
                           |
                           v
+-------------------------------------------------------+
| 3. First-Stage Bootloader (FSBL) from SPI NOR Flash   |
|    - Fetched via SPI interface                        |
|    - Configures clock generators / PLLs               |
|    - Calibrates DDR3 memory controller                |
|    - Initializes console UART (if enabled in build)   |
+-------------------------------------------------------+
                           |
                           v
+-------------------------------------------------------+
| 4. Secondary Bootloader (Das U-Boot)                  |
|    - Executed from RAM                                |
|    - Checks bootcmd / environment parameters          |
|    - Reads kernel image from NAND flash (or USB)      |
+-------------------------------------------------------+
                           |
                           v
+-------------------------------------------------------+
| 5. Linux Kernel & User Environment                    |
|    - Boots STLinux kernel                             |
|    - Mounts root filesystem (NAND flash)              |
|    - Launches GVT / Vivo middleware application       |
+-------------------------------------------------------+
```

---

## Secure Boot & Security State Uncertainty

A critical unknown is whether the hardware security subsystem on **this specific physical unit** enforces cryptographic signatures:
1. **Unfused / Development State:** If OTP fuses were left open or in production-open mode, the BootROM and U-Boot will execute any valid binary.
2. **Fused / Production State:** If OTP fuses enforce RSA signature verification, the BootROM will refuse to execute unsigned FSBL code from NOR flash.

### Strategic Implication
- We must determine whether signature checks are active before attempting any modifications to nonvolatile flash.
- Preserving pristine, multi-pass verified dumps of all nonvolatile memories (SPI NOR and NAND) is mandatory before executing any write operations.
