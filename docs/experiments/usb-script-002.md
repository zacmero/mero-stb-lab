# USB-SCRIPT-002 — conventional U-Boot script discovery

**Status: prepared and host-validated; receiver execution NOT tested.**

This is the current software-only experiment. BOOT-CHAIN-001's physical
UART/flash investigation is deferred for this attempt; a multimeter, UART
adapter, soldering or new photographs are not prerequisites for USB-SCRIPT-002.

## Canonical files

- [Payload, explanation and primary references](../../probes/usb-script-002/README.md)
- [Gemini deployment instructions](../../probes/usb-script-002/GEMINI_TASK.md)
- [Readable commands](../../probes/usb-script-002/prepared/boot.cmd)
- [Builder](../../probes/usb-script-002/build_probe.py)
- [Automated host tests](../../probes/usb-script-002/test_build_probe.py)
- [Manifest](../../probes/usb-script-002/prepared/manifest.json)
- [Checksums](../../probes/usb-script-002/prepared/SHA256SUMS)

Four identical legacy SCRIPT images are already built, at `boot.scr`,
`boot.scr.uimg`, `boot/boot.scr`, and `boot/boot.scr.uimg` within
`probes/usb-script-002/prepared/usb-files/`. Copy that directory's CONTENTS to
the verified existing USB filesystem, not the enclosing directory or a ZIP.
No formatting or raw block-device writes are needed.

The previous zero-byte `.bin` filename probe did not demonstrate a USB loader:
the same vendor update screen appeared without the stick. Do not rerun the old
formatting scripts or treat the USB LED as evidence of filesystem access.

## Hypothesis and observation

A stock loader MIGHT recognize conventional U-Boot scripts. U-Boot itself,
USB script discovery, supported commands, actual boot order and security state
remain unconfirmed on this particular receiver. This test is NOT Linux,
a firmware installer, or a demonstrated security bypass.

The commands request exact console markers, 12 seconds of initial delay, and
three pings to the PC separated by requested 3- and 7-second pauses. They contain
no flash/storage-write or persistent-environment-save commands. Actual behavior
of the unknown vendor loader is not guaranteed.

Default addresses: PC `192.168.1.97`, receiver `192.168.1.134`, mask
`255.255.255.0`. Confirm current ownership before deployment. Ethernet is
required for the network marker; TV output is useful but console output may be
serial-only. Restore the heat spreader and thermal contact before power-on.

Start a fresh bounded capture immediately before the boot. A receiver-to-PC
marker is observable on this LAN; earlier PC captures could not rule out
receiver-to-router unicast on a switch. Network silence in the old notes is
not evidence that the receiver never contacts external servers.

## Local validation

```bash
cd probes/usb-script-002
python3 -m unittest -v test_build_probe.py
python3 build_probe.py verify prepared
(cd prepared && sha256sum -c SHA256SUMS)
```

All ten automated host tests passed during preparation, including byte-for-byte
reproduction of the supplied images and CRC/corruption tests. Host checks do
not establish device compatibility or hardware execution.

## Result — Physical Experiment

- **Tested at:** 2026-09-17 23:00 – 23:05 (Local Time)
- **Commit / Payload SHA-256:**
  - Commit: `b1938d85d067865f560b9f3efacaf39239f8afd9`
  - Script Image SHA-256: `75501f4bd3254807e23b08b0f4799ef7c323aa47857b8b6f9b8df9c7499cad4a`
- **Confirmed PC / Receiver / Interface:**
  - Observing PC: `192.168.1.97` on interface `enp5s0`
  - Receiver: `192.168.1.134` (MAC: `68:15:90:6b:81:96`)
- **USB Identity & Hash Verification:**
  - Partition: `/dev/sde1` (FAT32, label `MERO_STB`, UUID `D839-D0E8`)
  - Deployed paths verified on-stick:
    - `/README.TXT` (`cdd1f20833de1d7df1e25ad7c3363e0723352c4a84c15e28bd9f96c374b60d89`)
    - `/boot.scr` (`75501f4bd3254807e23b08b0f4799ef7c323aa47857b8b6f9b8df9c7499cad4a`)
    - `/boot.scr.uimg` (`75501f4bd3254807e23b08b0f4799ef7c323aa47857b8b6f9b8df9c7499cad4a`)
    - `/boot/boot.scr` (`75501f4bd3254807e23b08b0f4799ef7c323aa47857b8b6f9b8df9c7499cad4a`)
    - `/boot/boot.scr.uimg` (`75501f4bd3254807e23b08b0f4799ef7c323aa47857b8b6f9b8df9c7499cad4a`)
- **Heat Spreader Restored:** Yes, thermal interface and heat spreader seated during test.
- **Capture Running Before Cold Boot:** Yes, 180s bounded `tcpdump` active on `enp5s0`.
- **TV Display & UI Timing:** Standard boot sequence observed; no console text, no added 22-second delay, standard time to factory GVT/Vivo application UI.
- **Exact Console Marker / Pings:** None. Zero ICMP echo requests observed from `192.168.1.134`. The only receiver network activity was standard ARP request for the default gateway (`192.168.1.1`) at 23:01:50.
- **Local Capture Location:** `probes/usb-script-002/captures/usb-script-002.pcap` (preserved locally, ignored from git).
- **No-Stick Control:** Not required; no positive marker or deviation from baseline boot occurred.
- **Interpretation:** **NEGATIVE (No observable execution).** The resident stock bootloader does not automatically load or execute conventional legacy U-Boot scripts from `/boot.scr`, `/boot.scr.uimg`, `/boot/boot.scr`, or `/boot/boot.scr.uimg` on FAT32 USB storage during cold boot.

This result confirms that speculative USB script discovery does not provide an execution entry point on this Sagemcom DSI74 V2 firmware. Physical boot-chain archaeology (UART discovery and SPI NOR flash examination under BOOT-CHAIN-001) remains the required technical path to code execution.
