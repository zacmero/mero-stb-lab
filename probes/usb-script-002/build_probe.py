#!/usr/bin/env python3
"""Build a finite, non-flashing legacy U-Boot script probe.

Uses only Python's standard library. Does not access block devices, format disks,
mount filesystems, or copy to a USB stick. Output is a normal local directory.

This is NOT a Linux kernel, firmware update, or proven DSI74 boot method.
"""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
from pathlib import Path
import struct
import sys
import zlib

HEADER = struct.Struct('>7I4B32s')
MAGIC = 0x27051956
STAMP = 1789603200  # Fixed timestamp for reproducible builds (2026-09-17 UTC).
OS_LINUX = 5       # A legacy header tag, NOT evidence of a Linux kernel.
ARCH_SH = 9
TYPE_SCRIPT = 6
NAME = b'MERO USB-SCRIPT-002'
TARGETS = ('boot.scr', 'boot.scr.uimg', 'boot/boot.scr', 'boot/boot.scr.uimg')


def validate_addresses(pc: str, receiver: str, mask: str) -> None:
    host = ipaddress.IPv4Address(pc)
    box = ipaddress.IPv4Address(receiver)
    subnet = ipaddress.IPv4Network(f'{receiver}/{mask}', strict=False)
    for address in (host, box):
        if address.is_multicast or address.is_unspecified or address.is_loopback:
            raise ValueError('Use ordinary unicast LAN addresses.')
        if address not in subnet or address in (subnet.network_address, subnet.broadcast_address):
            raise ValueError('Both addresses must be usable hosts in the same subnet.')
    if host == box:
        raise ValueError('The PC and receiver addresses must be different.')


def script_text(pc: str, receiver: str, mask: str) -> str:
    validate_addresses(pc, receiver, mask)
    # No branch/loop syntax: keep the script simple for older U-Boot parsers.
    # All environment changes are volatile under normal U-Boot semantics.
    # Save and restore the three networking variables used by this probe.
    return '\n'.join([
        'echo MERO_STB_USB_SCRIPT_002_START',
        'sleep 12; echo MERO_P2_DELAY_DONE',
        'version; echo MERO_P2_VERSION_DONE',
        'printenv bootcmd bootargs; echo MERO_P2_ENV_DONE',
        'setenv mero_p2_ip ${ipaddr}',
        'setenv mero_p2_mask ${netmask}',
        'setenv mero_p2_retry ${netretry}',
        f'setenv ipaddr {receiver}',
        f'setenv netmask {mask}',
        'setenv netretry no',
        'echo MERO_STB_USB_SCRIPT_002_PING_1',
        f'ping {pc}; echo MERO_P2_PING_DONE',
        'sleep 3; echo MERO_P2_GAP_DONE',
        'echo MERO_STB_USB_SCRIPT_002_PING_2',
        f'ping {pc}; echo MERO_P2_PING_DONE',
        'sleep 7; echo MERO_P2_GAP_DONE',
        'echo MERO_STB_USB_SCRIPT_002_PING_3',
        f'ping {pc}; echo MERO_P2_PING_DONE',
        'setenv ipaddr ${mero_p2_ip}',
        'setenv netmask ${mero_p2_mask}',
        'setenv netretry ${mero_p2_retry}',
        'setenv mero_p2_ip',
        'setenv mero_p2_mask',
        'setenv mero_p2_retry',
        'echo MERO_STB_USB_SCRIPT_002_END',
        '',
    ])


def encode_script(text: str) -> bytes:
    source = text.encode('ascii')
    # Legacy SCRIPT payload: network-endian component size, zero terminator,
    # then script text. Last component does not require padding.
    payload = struct.pack('>II', len(source), 0) + source
    data_crc = zlib.crc32(payload) & 0xffffffff
    fields = (MAGIC, 0, STAMP, len(payload), 0, 0, data_crc,
              OS_LINUX, ARCH_SH, TYPE_SCRIPT, 0, NAME.ljust(32, b'\0'))
    zero_header = HEADER.pack(*fields)
    header_crc = zlib.crc32(zero_header) & 0xffffffff
    return HEADER.pack(*(fields[:1] + (header_crc,) + fields[2:])) + payload


def decode_script(blob: bytes) -> str:
    if len(blob) < HEADER.size + 8:
        raise ValueError('Truncated image.')
    values = list(HEADER.unpack(blob[:HEADER.size]))
    magic, header_crc, stamp, size, load, entry, data_crc = values[:7]
    os_id, arch, image_type, compression = values[7:11]
    if (magic, os_id, arch, image_type, compression) != (MAGIC, OS_LINUX, ARCH_SH, TYPE_SCRIPT, 0):
        raise ValueError('Unexpected legacy image type/architecture/compression.')
    if load != 0 or entry != 0:
        raise ValueError('This probe must not specify a native-code load/entry address.')
    values[1] = 0
    if (zlib.crc32(HEADER.pack(*values)) & 0xffffffff) != header_crc:
        raise ValueError('Header CRC mismatch.')
    payload = blob[HEADER.size:]
    if len(payload) != size or (zlib.crc32(payload) & 0xffffffff) != data_crc:
        raise ValueError('Data length/CRC mismatch.')
    length, terminator = struct.unpack('>II', payload[:8])
    if terminator != 0 or length != len(payload) - 8 or length == 0:
        raise ValueError('Invalid script component table.')
    return payload[8:].decode('ascii')


def audit_script(text: str) -> None:
    allowed = {'echo', 'sleep', 'version', 'printenv', 'setenv', 'ping'}
    env_vars = {'ipaddr', 'netmask', 'netretry', 'mero_p2_ip', 'mero_p2_mask', 'mero_p2_retry'}
    lines = text.splitlines()
    for line in lines:
        if not line:
            continue
        if any(c in line for c in ('`', '|', '&', '\x00')) or len(line) >= 128:
            raise ValueError('Unexpected syntax or overlong command.')
        for command in line.split(';'):
            words = command.split()
            if not words or words[0] not in allowed:
                raise ValueError(f'Command not permitted: {command}')
            if words[0] == 'setenv' and (len(words) < 2 or words[1] not in env_vars):
                raise ValueError('Unexpected environment variable.')
    if sum(line.startswith('ping ') for line in lines) != 3:
        raise ValueError('Expected exactly three ping commands.')


def write_bundle(out: Path, pc: str, receiver: str, mask: str) -> None:
    if out.exists():
        raise ValueError(f'{out} already exists. Use a NEW output directory; nothing was overwritten.')
    text = script_text(pc, receiver, mask)
    audit_script(text)
    blob = encode_script(text)
    if decode_script(blob) != text:
        raise ValueError('Image round-trip failed.')
    out.mkdir(parents=True)
    usb = out / 'usb-files'
    usb.mkdir()
    for name in TARGETS:
        target = usb / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(blob)
    (out / 'boot.cmd').write_text(text, encoding='ascii')
    (usb / 'README.TXT').write_text(
        'MERO-STB USB-SCRIPT-002\n'
        'Experimental U-Boot script discovery test. NOT Linux or firmware.\n'
        'No flash/storage-write or persistent-environment-save commands.\n'
        'DSI74 U-Boot presence and USB script discovery are UNCONFIRMED.\n',
        encoding='ascii',
    )
    manifest = {
        'experiment': 'USB-SCRIPT-002',
        'kind': 'legacy U-Boot SCRIPT, not KERNEL and not FIRMWARE',
        'target_hardware_execution_tested': False,
        'stock_bootloader_identified': False,
        'usb_autoload_confirmed': False,
        'pc_ip': pc, 'receiver_ip': receiver, 'netmask': mask,
        'delay_seconds_if_sleep_supported': 22,
        'ping_count_commands': 3,
        'script_bytes': len(text.encode('ascii')),
        'image_bytes': len(blob),
        'image_sha256': hashlib.sha256(blob).hexdigest(),
        'image_type': 6, 'architecture': 9,
        'header_and_data_crc_verified': True,
        'source_allowlist_verified': True,
        'persistent_write_commands': [],
    }
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    paths = [out / 'boot.cmd', out / 'manifest.json', usb / 'README.TXT']
    paths += [usb / name for name in TARGETS]
    checksums = [f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(out).as_posix()}' for p in paths]
    (out / 'SHA256SUMS').write_text('\n'.join(checksums) + '\n', encoding='ascii')
    print(json.dumps(manifest, indent=2))
    print(f'Built regular files in: {out.resolve()}')
    print('No USB drive was accessed. No receiver was flashed or booted.')


def verify_bundle(out: Path) -> None:
    manifest = json.loads((out / 'manifest.json').read_text())
    expected = script_text(manifest['pc_ip'], manifest['receiver_ip'], manifest['netmask'])
    audit_script(expected)
    if (out / 'boot.cmd').read_text(encoding='ascii') != expected:
        raise ValueError('Source differs from this builder template.')
    for name in TARGETS:
        blob = (out / 'usb-files' / name).read_bytes()
        if decode_script(blob) != expected:
            raise ValueError(f'Script content mismatch: {name}')
        if hashlib.sha256(blob).hexdigest() != manifest['image_sha256']:
            raise ValueError(f'Image hash mismatch: {name}')
    print('PASS: 4 images; legacy headers, both CRCs, source, command allowlist and SHA-256.')
    print('This verifies file construction only, NOT DSI74 compatibility or execution.')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    build = sub.add_parser('build')
    build.add_argument('--pc-ip', required=True)
    build.add_argument('--receiver-ip', required=True)
    build.add_argument('--netmask', default='255.255.255.0')
    build.add_argument('--output', type=Path, required=True)
    check = sub.add_parser('verify')
    check.add_argument('directory', type=Path)
    args = parser.parse_args()
    try:
        if args.action == 'build':
            write_bundle(args.output, args.pc_ip, args.receiver_ip, args.netmask)
        else:
            verify_bundle(args.directory)
    except (ValueError, OSError, KeyError, UnicodeError, struct.error) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
