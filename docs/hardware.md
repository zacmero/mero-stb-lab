# Target Hardware Profile: Sagemcom DSI74 (STiH237)

## Overview
The Sagemcom DSI74-family set-top box is an embedded Linux TV receiver originally deployed by Brazilian telecommunications operator GVT. The hardware platform is built upon STMicroelectronics silicon.

## Specifications

| Component | Detail |
| :--- | :--- |
| **SoC** | STMicroelectronics STiH237 ("Cardiff") |
| **CPU Architecture** | SuperH SH-4 / ST40-300 core |
| **System Memory** | 256 MB DDR SDRAM |
| **Boot Flash** | Serial SPI / NOR Flash (hosts primary bootloader / U-Boot) |
| **Storage Flash** | Parallel NAND Flash (stores OEM system partitions, rootfs, middleware) |
| **Network** | 10/100 Mbps Fast Ethernet (RJ-45) |
| **USB** | 1x USB 2.0 Host Type-A port |
| **Video Outputs** | HDMI, Analog Composite (CVBS + Stereo RCA) |
| **Audio Outputs** | Digital Optical S/PDIF, Analog Stereo |
| **RF / Tuner** | DVB-S2 satellite tuner input + loop-through |
| **Power Input** | 12V DC external barrel adapter |

## Thermal Constraints
> **Warning:** The STiH237 SoC generates significant heat under normal operation. The thermal pad and aluminum heatsink must remain firmly seated during all bench testing and boot sequences to prevent thermal throttling or silicon degradation.

## Memory Devices & Flash Topology
1. **SPI NOR Boot Flash:** Responsible for early SoC initialization, DDR controller configuration, pinmux configuration, and executing the secondary bootloader (typically a customized Das U-Boot).
2. **NAND Storage:** Contains the OEM root filesystem, kernel images, and operator configurations.
