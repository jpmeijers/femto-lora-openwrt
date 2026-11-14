# Public build

Build identifier: `public-v2`, prepared 2026-11-14.
OpenWrt 23.05 branch / Linux 5.15.211, MIPS little-endian 24kc.
Exact upstream revisions and regeneration commands: `docs/BUILD.md`.
Matching build configuration and board source: `board/config.build` and
`board/openwrt.patch` at Git tag `public-v2` (commit `20f41a1`). HAL feed patches:
`board/lora-hal-*.patch` at the same tag. Later development source can differ.
Package versions: `packages.manifest`.

These files were built from source, not exported from a running device.
No device EUI is embedded. Runtime discovery prefers the factory EEPROM cache
and falls back to a locally administered EUI derived from the factory Wi-Fi MAC.
The EU reference TX table is included; a valid factory cache takes precedence.
Wi-Fi and forwarding start disabled; downlinks default to enabled. Only EU
hardware is supported. Firmware SHA256 values are in `SHA256SUMS`.


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

Synthetic host tests cover CRC validation, EUI recovery/fallback, region detection
and conflicting metadata. Runtime default and regional-guard validation results
are recorded below. Public files and extracted rootfs are checked against known
private identifiers and credentials; no generated host private keys are included.

Published UBI root volume was matched to the audited Squashfs; both uImage
CRCs and the embedded RAM CPIO were checked as part of the privacy audit.

The public-v2 image booted through NAND sysupgrade with private settings and SSH
keys unchanged. The board helper recovered the existing factory EUI and all 16
gain entries on the EU unit. Default generation enabled downlinks and preferred
the cached table. Tests rejected non-EU/conflicting metadata and required EU
confirmation for unknown metadata; the reference-table fallback generated
successfully. The automatic-table plan initialized the concentrator on hardware.
No end-device downlink RF power measurement or round-trip test is claimed.
The read-only backup helper captured a small partition in both data-only and
raw-with-OOB formats; decompressed sizes and SHA256 matched the manifest.
