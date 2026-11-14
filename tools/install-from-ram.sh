#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-only
# Run on the gateway, from the matching initramfs image. Destructive.
set -eu
cd "${1:-/tmp/femto-firmware}"
[ "${2:-}" = '--erase-firmware1' ] || {
 echo 'Usage: sh install-from-ram.sh /tmp/femto-firmware --erase-firmware1' >&2
 echo 'Irreversible: overwrites firmware1. No known factory rollback.' >&2
 exit 1
}
[ "$(cat /tmp/sysinfo/board_name)" = 'gemtek,wlrgfm-100' ] || { echo 'Wrong board' >&2; exit 1; }
root_type=$(awk '$2 == "/" { print $3; exit }' /proc/mounts)
case "$root_type" in rootfs|tmpfs|ramfs) ;; *) echo 'STOP: boot RAM recovery first' >&2; exit 1 ;; esac
if awk '$1 ~ /^\/dev\/(ubi|ubiblock)/ { found=1 } END { exit !found }' /proc/mounts; then
 echo 'STOP: a NAND UBI filesystem is mounted; do not erase it' >&2; exit 1
fi
grep -Eq '^mtd3: 00800000 00020000 "kernel"$' /proc/mtd || exit 1
grep -Eq '^mtd4: 01600000 00020000 "ubi"$' /proc/mtd || exit 1
[ -s kernel.bin ] && [ -s rootfs.ubi ] && [ -s SHA256SUMS ]
[ "$(wc -c < kernel.bin)" -le 8388608 ]
[ "$(wc -c < rootfs.ubi)" -le 23068672 ]
# Check exactly the two flash payloads, not missing host-only recovery files.
awk '$2 == "kernel.bin" || $2 == "rootfs.ubi" { print; n++ } END { if(n!=2) exit 1 }' SHA256SUMS > /tmp/femto-install-hashes
sha256sum -c /tmp/femto-install-hashes
[ "$(hexdump -n 4 -e '4/1 "%02x"' kernel.bin)" = 27051956 ]
[ "$(hexdump -n 4 -e '4/1 "%02x"' rootfs.ubi)" = 55424923 ]
# Retain protected-partition hashes locally, without printing identifiers.
sha256sum /dev/mtd0 /dev/mtd1 /dev/mtd2 > /tmp/femto-protected-before.sha256
if [ -e /sys/class/ubi/ubi0/mtd_num ]; then
 [ "$(cat /sys/class/ubi/ubi0/mtd_num)" = 4 ] || exit 1
 ubidetach /dev/ubi_ctrl -m 4
fi
ubiformat /dev/mtd4 -y -f rootfs.ubi
# Kernel is written last. No saved U-Boot environment changes.
mtd write kernel.bin kernel
size=$(wc -c < kernel.bin)
head -c "$size" /dev/mtd3 > /tmp/femto-kernel-readback
expected=$(sha256sum kernel.bin); actual=$(sha256sum /tmp/femto-kernel-readback)
[ "${expected%% *}" = "${actual%% *}" ] || { echo 'Kernel readback failed; stay in RAM recovery' >&2; exit 1; }
sha256sum -c /tmp/femto-protected-before.sha256
sync
echo 'Firmware written. Reboot manually, then wait for first boot to finish.'
