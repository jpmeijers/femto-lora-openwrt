# Sources and licenses

This is an independent experimental port, not an official OpenWrt or Gemtek release.
New project glue, scripts and documentation are distributed under GPL-2.0-only.
Existing components retain their upstream licenses and copyright notices.

- OpenWrt: GPL-2.0; pinned revision in `tools/apply-board.sh`.
- Parallel NAND driver: imported from X-Wrt revision
  [`372c1d30d0be58b70092710a5c298a321fb42318`](https://github.com/x-wrt/x-wrt/tree/372c1d30d0be58b70092710a5c298a321fb42318/target/linux/ramips/files/drivers/mtd/maps), then adapted to Linux 5.15.
  The driver declares GPL. Its corresponding modified source is included
  in `board/openwrt.patch`; no proprietary vendor firmware is distributed.
- Semtech `lora_gateway` 5.0.1 and `packet_forwarder`: BSD-3-Clause.
  The packet forwarder source revision and archive SHA256 are in the
  package recipe inside `board/openwrt.patch`.
- Optional Femto Basic Station: Semtech Basic Station 2.0.6, BSD-3-Clause,
  with its private LoRa HAL 5.0.1 and upstream Station changes (BSD-3-Clause).
  The pinned archive hashes and build modifications are in `board/openwrt.patch`.
- LuCI and other OpenWrt packages retain their own upstream licenses.
  Package source locations, archive hashes and patches are recorded in the
  pinned OpenWrt and feed recipes. See `docs/BUILD.md` for obtaining sources.

No factory firmware, hardware dump, Wi-Fi password, private signing key, device
identifier, or original device photograph is included. A numeric reference EU
TX gain table is included; it contains no device identity or credentials.
