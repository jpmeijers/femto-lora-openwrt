# Public build

Build identifier: `public-v1`, prepared 2026-11-14.
OpenWrt 23.05 branch / Linux 5.15.211, MIPS little-endian 24kc.
Exact upstream revisions and regeneration commands: `docs/BUILD.md`.
Matching build configuration and board source: `board/config.build` and
`board/openwrt.patch`. HAL feed patches: `board/lora-hal-*.patch`.
Package versions: `packages.manifest`.

These files were built from source, not exported from a running device.
Default gateway EUI is blank, no per-unit TX gain table is included, Wi-Fi
and LoRa are disabled, and build metadata uses generic builder/host names.
The TX-enable guard requires a user-supplied calibration plan. Firmware
SHA256 values are in `SHA256SUMS`.

The underlying port was exercised on one EU unit; this remains an unsupported
experimental build, not a generally certified hardware release. See the
README and board notes for tested behavior and remaining limitations.
**Flash at your own risk. No known tested factory rollback exists.**

## Validation of these public artifacts

The exact public image was installed through NAND sysupgrade and booted on the
EU development unit. Existing private Wi-Fi, LoRa configuration and SSH host
key hashes were preserved. The first-install helper refused execution from a
running NAND root before performing writes. Its complete factory-to-RAM install
sequence has not been tested as an automated procedure on pristine factory
firmware. The underlying manual write sequence was used during bring-up.

The default configuration rejects a blank EUI and rejects TX without a supplied
calibration plan. Generic receive-only concentrator startup passed on hardware, separately
from the private per-unit operating configuration. Public images
and patches passed a scan against known private identifiers and credentials;
the extracted rootfs has no nonempty generated SSH host private keys.

Published UBI root volume was matched to the audited Squashfs; both uImage
CRCs and the embedded RAM CPIO were checked as part of the privacy audit.
