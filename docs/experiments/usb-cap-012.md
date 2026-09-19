# USB-CAP-012: Application-Visible USB and Local-File Probe

## Status

**COMPLETED — NEGATIVE for application-visible file access; OS-level USB support remains unknown.**

## Objective

Determine whether the demonstrated Ekioh application runtime can read USB storage or harmless local OS identity files. Also record input events from a USB keyboard if one is available.

This experiment distinguishes application-runtime access from OS-level USB support. A negative application result does not establish that Linux failed to mount or use the device.

## Probe

The APP-HUB-010 module runs automatically and uses both `XMLHttpRequest` and Ekioh `getURL(url, callback)`. It performs 12 read-only cycles at 15-second intervals against:

- `/proc/version`
- `/etc/os-release`
- `/etc/hostname`
- the inert marker `MERO_USB_012.txt` under five bounded, common removable-media mount paths
- `usb:///MERO_USB_012.txt`

The module never writes to the receiver, invokes an updater, changes boot state, or requests privileged native methods. It reports response status, bounded response content, marker detection, and keyboard event codes.

## Preparation

1. Copy `probes/usb-cap-012/MERO_USB_012.txt` to the root of the FAT32 `MERO_STB` flash drive.
2. Safely eject the drive from the workstation.
3. Insert it into the powered-off receiver.
4. Cold boot the receiver.
5. Launch Vivo Play once after the host harness reports ready.
6. If testing USB HID, press a few keyboard keys only after the probe screen appears.

## Evidence requirements

A USB read is positive only if the receiver reports the exact marker `MERO-USB-CAP-012-7B3D9E21`. A local-file read is positive only if the receiver reports actual bounded content. Status `0`, an exception, or an empty body is negative for that API and URI only.

Receiver-originated reports and network cleanup verification remain canonical. Screen text alone is not evidence.

## Hardware result

The FAT32 `MERO_STB` drive was present from cold boot. Its root marker matched the repository copy at SHA-256 `c65b6fbaf02e8e7c3c03a952965296d642fcefda8c0454047355a119ba06329b` before safe unmount from the workstation.

Receiver `192.168.1.62` loaded `USB-CAP-012-v1` at `2026-09-19T22:21:09.532822Z`. Five complete cycles produced identical results:

- `XMLHttpRequest` threw `DOMException` for every `file:` and `usb:` URI.
- Native `getURL` returned `success=false` with zero content for every candidate.
- `/proc/version`, `/etc/os-release`, and `/etc/hostname` were not readable through either tested API.
- No tested removable-media path returned `MERO-USB-CAP-012-7B3D9E21`.
- No USB keyboard was tested in this session; USB HID remains a separate queued experiment.

This establishes that the tested Ekioh application APIs and URI forms did not expose local files or the mounted-media marker. It does not establish whether Linux detected or mounted the USB drive, whether another untested mount path exists, or whether firmware/update services can read USB independently of Ekioh.

The host requested cleanup at `2026-09-19T22:22:15.540911Z`. Run-owned processes and firewall state were removed. Verification found zero `MNC005` rules; both `send_redirects` sysctls returned to `1`; gateway, DNS, and HTTPS checks passed.

Final probe hashes:

- `web/app-hub-module.js`: `2bec1cbfd9548d5bd1ea12c542a47f0ce6c1fbb420d362bd7c6c9d5dd95d46f0`
- `web/app-hub-manifest.json`: `58c2a3ee54bd86c878ed8e76ae539f19fbb08ff1c7805b1770d2caf40841c6bd`
