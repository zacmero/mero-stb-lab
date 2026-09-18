# Execute USB-SCRIPT-002 from this repository

From the `mero-stb-lab` repository root, use:

```bash
cd probes/usb-script-002
python3 -m unittest -v test_build_probe.py
python3 build_probe.py verify prepared
(cd prepared && sha256sum -c SHA256SUMS)
```

The four ready-to-copy script images are already tracked in Git. Building is
needed only if the LAN addresses have changed. Do not run the old
`tools/prepare-usb-probe.sh` or `scripts/prepare-usb-probe.sh`: those belong to
USB-PROBE-001 and are not the deployment method for this test.

A capture that was started while preparing the stick may have expired after
180 seconds. Check it and restart immediately before the physical boot; do not
start the timer and then spend several minutes preparing files. Keep captures
local in this directory's ignored `captures/` folder. The experiment record is
`../../docs/experiments/usb-script-002.md`.


I authorize preparation of my already-used ~129 MB MERO_STB USB stick for this bounded, speculative U-Boot SCRIPT test. Do not ask for a multimeter or UART adapter and do not repeat broad port scans. This is NOT permission to write the receiver's flash or unrelated disks.

1. Read README.md and prepared/boot.cmd. Inspect the existing repository before adding files; use one canonical experiment note and preserve unrelated work.
2. Run `ip -4 addr`, `ip route`, `ip neigh`, `lsblk -o NAME,PATH,SIZE,MODEL,TRAN,RM,FSTYPE,LABEL,MOUNTPOINTS`, and `findmnt` as appropriate. Identify the current receiving PC/interface and the previously identified USB drive. Default payload target is PC 192.168.1.97, receiver 192.168.1.134/24. Verify .134 still belongs to 68:15:90:6b:81:96 before using it; do not hijack an address assigned to another device. Ask only if an essential identity remains genuinely ambiguous.
3. Verify the bundle: `python3 build_probe.py verify prepared` and `(cd prepared && sha256sum -c SHA256SUMS)`. If current addresses differ, rebuild with build_probe.py into a new LOCAL output directory and verify that bundle instead. No additional Python packages are needed.
4. Do not reformat the stick. On its positively identified mounted filesystem, remove ONLY the four previous zero-byte .bin probes. Inspect any nonempty file rather than deleting it blindly. Copy the CONTENTS of prepared/usb-files/ (or the rebuilt equivalent) to the USB root. Keep the source/generator/manifests in the repository, not as fake firmware.
5. Verify every copied script's size/hash from the USB itself. Each default image is 873 bytes with SHA-256 75501f4bd3254807e23b08b0f4799ef7c323aa47857b8b6f9b8df9c7499cad4a. A regenerated bundle has its own manifest/hash. Run sync and cleanly unmount that USB filesystem.
6. State exactly what is deployed: four copies of a legacy U-Boot SCRIPT at conventional paths. No kernel, Linux image, flash update or security bypass is deployed. No device compatibility has been demonstrated. These filenames are documented U-Boot conventions, NOT confirmed Sagemcom paths.
7. Prepare a bounded 180-second capture on the actual PC Ethernet interface BEFORE I power on the receiver. Capture ARP and ICMP echo requests addressed TO the PC, not a broad scan. Stop any existing scans. Do not serve firmware, change router settings, disable firewalls or open external ports. Save any PCAP locally, with repository ignore rules appropriate for device/network details.
8. Tell me to restore the heat-spreader/thermal contact, connect the receiver to the same LAN for the network marker, insert the safely unmounted stick with power off, and cold-boot once. TV helps, but the script's stdout may be serial-only. Look for the exact MERO marker, requested extra delay, or three device-to-PC ping commands with 3- and 7-second gaps (subject to timeout/retry delays). The script may run more than once if the loader scans multiple paths.
9. Interpret the result honestly. Matching network/console markers are evidence of execution; verify an apparent hit with a no-stick control. Delay alone is weak evidence. The USB LED or old vendor update screen is not success. No observable marker means this probe did not demonstrate execution; stop this attempt rather than invent new recovery names or declare Linux impossible.

Do not claim zero electrical/firmware risk. The supplied script has no storage-write or persistent-environment-save commands, but stock loader behavior is unverified. Do not add NAND/SPI commands, saveenv, arbitrary memory writes, reboot loops, or malformed updater files.

Deliver: verified on-stick file listing/hashes, exact capture command, one physical boot instruction, and an honest experiment result entry. No new schematic/photo/tool-shopping loop.
