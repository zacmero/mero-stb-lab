# Buildroot Configuration: Mero-STB Userspace

## Target Profile: Mero-STB v0.1

The userspace target for the Sagemcom DSI74 (STiH237) is built using **Buildroot** to produce an ultra-lean, headless embedded Linux root filesystem.

---

## Architectural Specifications

- **Target Architecture:** SuperH (SH-4 / ST40)
- **Target Variant:** `sh4` (little-endian)
- **C Library:** `uClibc-ng` or `musl` (for minimal RAM footprint)
- **Init System:** BusyBox `init`

---

## Core Package Manifesto

| Package | Utility / Purpose |
| :--- | :--- |
| **BusyBox** | Core shell (`/bin/sh`), standard UNIX utilities, lightweight syslog |
| **Dropbear** | Ultra-lightweight SSH server and `scp` client |
| **udhcpc** | Automatic IPv4 DHCP network configuration |
| **iproute2** | Modern network interface routing and control (`ip` command) |
| **procps-ng** | Process monitoring (`ps`, `top`, `free`) |
| **e2fsprogs / dosfstools** | Filesystem maintenance for USB storage |
| **fbset / fbv** | Direct framebuffer inspection for HDMI/CVBS outputs |

---

## Development Milestones

1. **Milestone 1: Headless Network Node (Primary Target)**
   ```bash
   ssh root@192.168.1.134
   uname -a
   cat /proc/cpuinfo
   ```
2. **Milestone 2: Framebuffer & Display**
   - DirectFB / console text on HDMI and analog composite (CVBS).
3. **Milestone 3: Hardware Peripheral Control**
   - Front-panel display driver (PT6958 communication over 3-line serial).
   - Front-panel buttons / IR remote mapping.
