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

## Result — fill only after the physical experiment

- Tested at: pending
- Commit/payload SHA-256: pending
- Confirmed PC/receiver/interface: pending
- USB identity and on-stick hash verification: pending
- Heat spreader restored: pending
- Capture running before cold boot: pending
- TV wording and time to normal UI: pending
- Exact console marker or matching receiver-to-PC ping sequence: pending
- Local capture location (do not publish raw PCAP): pending
- No-stick control if an apparent hit occurs: pending
- Interpretation: pending; do not label as executed or Linux installed yet

An exact marker or a reproducible new receiver-originated ping sequence merits
a no-stick control and further analysis. A delay alone is inconclusive. No
marker means only that this test demonstrated no observable execution.

The older notes' definite U-Boot, NAND/NOR ordering, and 1.8/3.3 V test-pad
claims are hypotheses, not verified board-level facts. This test uses none of
those electrical assumptions.
