#!/usr/bin/env bash
#
# prepare-usb-probe.sh
# Safely prepares a removable USB flash drive for MERO-STB USB recovery probe testing.
#
# Usage:
#   sudo ./scripts/prepare-usb-probe.sh /dev/sdX
#
set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <target-device> (e.g. /dev/sde)" >&2
    exit 1
fi

TARGET_DEV="$1"

if [[ ! -b "$TARGET_DEV" ]]; then
    echo "Error: $TARGET_DEV is not a valid block device." >&2
    exit 1
fi

# Sanity check: must be a removable USB device
IS_REMOVABLE=$(lsblk -no RM "$TARGET_DEV" | head -n 1 | tr -d '[:space:]')
TRANSPORT=$(lsblk -no TRAN "$TARGET_DEV" | head -n 1 | tr -d '[:space:]')

echo "=== Target Device Information ==="
lsblk -o NAME,PATH,SIZE,MODEL,TRAN,RM,FSTYPE,MOUNTPOINTS "$TARGET_DEV"
echo "================================="

if [[ "$TRANSPORT" != "usb" && "$IS_REMOVABLE" != "1" ]]; then
    echo "ERROR: Target device $TARGET_DEV does not appear to be a removable USB drive." >&2
    echo "Aborting to prevent accidental data loss on internal storage." >&2
    exit 1
fi

read -rp "Are you absolutely sure you want to completely erase and repartition $TARGET_DEV? (type 'yes'): " CONFIRM
if [[ "$CONFIRM" != "yes" ]]; then
    echo "Aborted by user."
    exit 0
fi

echo "[1/6] Unmounting any active partitions on $TARGET_DEV..."
for part in $(lsblk -lno PATH "$TARGET_DEV" | tail -n +2); do
    if grep -qs "$part " /proc/mounts; then
        umount "$part"
    fi
done

echo "[2/6] Writing DOS/MBR partition table with bootable FAT32 partition..."
sfdisk "$TARGET_DEV" << 'EOF'
label: dos
start=2048, type=c, bootable
EOF

udevadm settle

PART_DEV="${TARGET_DEV}1"
if [[ ! -b "$PART_DEV" ]]; then
    # Handle devices like nvme or mmcblk where partition has 'p'
    PART_DEV="${TARGET_DEV}p1"
fi

echo "[3/6] Formatting $PART_DEV as FAT32 labeled MERO_STB..."
mkfs.vfat -F 32 -n "MERO_STB" "$PART_DEV"

echo "[4/6] Temporarily mounting $PART_DEV..."
MOUNT_DIR=$(mktemp -d /tmp/mero-stb-usb.XXXXXX)
mount "$PART_DEV" "$MOUNT_DIR"

echo "[5/6] Deploying probe payload files..."
cat << 'EOF' > "$MOUNT_DIR/README.TXT"
MERO-STB USB PROBE
Sagemcom DSI74 / STiH237
USB probe 001
EOF

touch "$MOUNT_DIR/update.bin"
touch "$MOUNT_DIR/upgrade.bin"
touch "$MOUNT_DIR/recovery.bin"
touch "$MOUNT_DIR/firmware.bin"

sync

echo "[6/6] Unmounting cleanly..."
umount "$MOUNT_DIR"
rmdir "$MOUNT_DIR"

echo "=== Probe USB Preparation Complete ==="
lsblk -f "$TARGET_DEV"
fdisk -l "$TARGET_DEV"
