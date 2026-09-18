# MERO-STB / USB-SCRIPT-002

**Status: built and locally format-checked; NOT executed on a Sagemcom receiver.**

This is a speculative, software-only **U-Boot script discovery test**. It is NOT a Linux kernel, install image, firmware update, or evidence of an unlocked bootloader.

The working hypothesis is: *perhaps the stock bootloader is U-Boot and scans USB storage for legacy scripts*. Neither part has been established on this DSI74 V2. The filenames here are documented U-Boot conventions, not confirmed Sagemcom filenames. This may simply be ignored. It is one bounded experiment, not a reason to keep trying arbitrary file names.

## What was actually built

`prepared/boot.cmd` is the complete, readable source. `prepared/usb-files/` contains four identical legacy SCRIPT images at conventional U-Boot paths and a descriptive text file.

- `boot.scr`
- `boot.scr.uimg`
- `boot/boot.scr`
- `boot/boot.scr.uimg`

The source requests a console marker, a 12-second pause, the U-Boot version/boot variables, and three ping commands to the PC with 3- and 7-second gaps. It then restores the three network environment variables it changed and prints an ending marker.

**If every command runs, the requested pauses total 22 seconds per execution, plus any network-command time.** A loader may try more than one path, so the pattern can repeat. Commands may be omitted from a vendor build. Optional diagnostic, sleep and ping commands are followed by an echo on the same line so a command failure need not abort a normal U-Boot script parser. The vendor implementation remains unverified. Console output might go only to UART and never to HDMI.

No flash-writing, USB-writing, environment-saving, reset, raw-memory-writing, kernel-loading, or firmware-installation command is present. The only settings changed are temporary U-Boot network variables, restored on a complete run. Ordinary U-Boot `setenv` does not persist them without `saveenv`. An unknown vendor loader is not a zero-risk environment, so no zero-risk claim is made.

## Default addresses: verify before use

The prebuilt files use the addresses observed in this conversation:

- Receiver: `192.168.1.134`
- PC to receive pings: `192.168.1.97`
- Netmask: `255.255.255.0`

Do not use a receiver IP reassigned to a different device. Check the current router lease or the receiver's confirmed IP/MAC while normally booted. The observed receiver MAC is `68:15:90:6b:81:96`; bootloader Ethernet configuration has not been observed and may differ.

If the addresses have changed, rebuild into a **new regular local directory**:

```bash
python3 build_probe.py build \
  --pc-ip 192.168.1.97 \
  --receiver-ip 192.168.1.134 \
  --netmask 255.255.255.0 \
  --output prepared-local
python3 build_probe.py verify prepared-local
```

The builder will not overwrite an existing output directory. It does not access disks, mount, format, or install anything.

## Local validation

```bash
python3 build_probe.py verify prepared
(cd prepared && sha256sum -c SHA256SUMS)
file prepared/usb-files/boot.scr
```

`file` recognizes a legacy U-Boot SuperH SCRIPT. The word **Linux** in that legacy image header is a format tag, not a claim that this contains Linux. The image type is SCRIPT (6), not KERNEL (2).

The validator checks header CRC, payload CRC, component size table, full source, restricted command set, and identical SHA-256 hashes of all copies. It does not verify the stock bootloader's existence or behavior.

If `mkimage` is already available, these independent checks are useful:

```bash
mkimage -l prepared/usb-files/boot.scr
mkimage -A sh -O linux -T script -C none \
  -n 'MERO USB-SCRIPT-002' -d prepared/boot.cmd /tmp/mero-independent.scr
```

The rebuilt header timestamp can differ; the extracted script should match. Do not install anything merely to repeat checks already completed.

## USB preparation

Use the existing ~129 MB `MERO_STB` stick. **No reformatting or raw `dd` is needed.** Identify its mounted filesystem by USB transport, label, capacity, and device identity, not just a guessed `/dev/sdX`.

Remove ONLY the four previous zero-byte `update.bin`, `upgrade.bin`, `recovery.bin`, `firmware.bin` probes from that verified USB filesystem. If any is nonempty or the identity is ambiguous, stop and inspect instead of deleting unrelated files.

Copy the CONTENTS of `prepared/usb-files/` to the root of the stick. Do not copy the ZIP itself as the test. Compare the four on-stick hashes with the manifest. Flush writes and safely unmount before unplugging.

Do not rename these scripts to `.bin` updater filenames, add random kernel/firmware images, add `saveenv`, change boot straps, or solder anything for this experiment.

## Physical test

Restore the heat-spreader and thermal contact; keep the hardware assembled for this powered test.

For the network marker, receiver and observing PC must be on the same non-isolated LAN. Use the actual receiving interface on that PC. The TV is useful to observe startup, but U-Boot may not initialize HDMI.

Stop other scans. Start capture BEFORE powering on the receiver:

```bash
sudo timeout --signal=INT 180 tcpdump -i enp5s0 -nn -e \
  'arp or (icmp and dst host 192.168.1.97 and icmp[0] = 8)'
```

Substitute the receiving interface and PC address if they changed. For evidence, Gemini may save a bounded PCAP locally instead and read it afterward. Do not adjust the router, disable firewalls, or open Internet-facing ports.

Cold-boot with the prepared stick; observe for up to three minutes. Record console/TV wording if any, time to normal UI, and any groups of receiver-originated ICMP echo requests. The 3- and 7-second gaps are requested gaps BETWEEN commands; exact packet timing depends on command completion/retries.

If Ethernet is unavailable, a repeatable extra delay is only a weak clue. The USB LED or the existing vendor 'updating' screen is not a positive result.

## Interpretation

- Exact `MERO_STB_USB_SCRIPT_002_START` output: strong evidence our script ran.
- A repeatable group of three receiver-originated ping attempts toward the configured PC that appears only with the stick: strong execution evidence; preserve capture and compare a no-stick control before declaring success.
- Delay alone: weak/inconclusive, because USB enumeration can also delay startup.
- Same vendor boot and no marker: **no observable execution of this probe**. This does NOT prove the box cannot boot Linux, that secure boot is enforced, or that all bootloader paths have been exhausted. Do not repeat blind filename guesses.

After testing, remove the stick with the receiver powered off and restart normally. This script issues no persistent write commands; do not interpret the normal vendor UI as a failed Linux install, since no Linux installation was attempted.

## Corrections to earlier project notes

- U-Boot presence, its command set, USB script autodiscovery, and a Linux vendor OS are unconfirmed on this unit.
- A schematic's supported boot options do not establish this unit's actual boot order/security configuration.
- The 3.3 V UART and 1.8 V JTAG claims in prior notes are NOT verified pin-level measurements. This test uses neither.
- Earlier PC captures on a switched LAN could miss receiver-to-router unicast. They cannot establish that the receiver does not contact servers. This script deliberately addresses packets TO the observing PC, avoiding that particular visibility problem.

## Primary references

- Legacy U-Boot script format / execution: https://docs.u-boot.org/en/latest/usage/cmd/source.html
- 2013 implementation: https://raw.githubusercontent.com/u-boot/u-boot/v2013.01/common/cmd_source.c
- Legacy header constants and layout: https://raw.githubusercontent.com/u-boot/u-boot/v2013.01/include/image.h
- Optional distro script filenames/search directories: https://docs.u-boot.org/en/latest/develop/distro.html
- Volatile environment and network settings: https://docs.u-boot.org/en/latest/usage/environment.html
- Sleep command: https://docs.u-boot.org/en/latest/usage/cmd/sleep.html
- STiH237 capabilities, not a Sagemcom boot recipe: https://www.st.com/en/digital-set-top-box-ics/stih237.html
- Switched Ethernet capture limits: https://wiki.wireshark.org/CaptureSetup/Ethernet

These establish mechanisms and limitations. They DO NOT establish DSI74 V2 support for USB-SCRIPT-002.
