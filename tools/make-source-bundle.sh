#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-only
# Bundle committed public code, pinned upstream trees and downloaded sources.
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
cd "$root"
[ -d openwrt/dl ] || { echo 'Run prepare.sh and build.sh download first' >&2; exit 1; }
mkdir -p private
stage=$(mktemp -d "$root/private/source-bundle.XXXXXX")
trap 'rm -rf "$stage"' EXIT
mkdir -p "$stage/femto-lora-openwrt" "$stage/upstream/openwrt" "$stage/upstream/packages" "$stage/upstream/luci"
# Only Git's reviewed public tree, never the surrounding workspace.
git archive HEAD | tar -x -C "$stage/femto-lora-openwrt"
git -C openwrt archive 33063b4ccf00d39393796499b23df55187b192dc | tar -x -C "$stage/upstream/openwrt"
git -C openwrt/feeds/packages archive f36055baca3ae8ba7f7bde3a9a6a6f3b1b9a82ea | tar -x -C "$stage/upstream/packages"
git -C openwrt/feeds/luci archive 3d39e8c38cfa276d5cdfad7105dbf47933eaed4f | tar -x -C "$stage/upstream/luci"
# Archives in dl are hash-checked upstream source downloads, not build outputs.
mkdir -p "$stage/downloads"
find openwrt/dl -maxdepth 1 -type f ! -name '*.hash' ! -name '*.lock' -exec cp -p '{}' "$stage/downloads/" \;
cat > "$stage/README.txt" <<'TXT'
Corresponding-source bundle for the experimental Femto OpenWrt port.
Project source, patches and build instructions: femto-lora-openwrt/.
Pristine pinned upstream trees: upstream/{openwrt,packages,luci}/.
Hash-checked downloaded component source archives: downloads/.
See the project docs/BUILD.md and NOTICE.md. Each upstream license applies.
The helper uses Git during preparation; git-fetch the pinned revisions, or
apply the project board patch to the supplied OpenWrt tree and use the
supplied feed trees through src-link feeds for an offline build. The separate
HAL patches must also be applied; copy the project configuration and place
downloads in openwrt/dl/. The normal prepare helper expects upstream Git
metadata; the bundled archives supply the code even without that metadata.
No private gateway dumps, credentials, hardware identifiers or keys are bundled.
TXT
out=${1:-private/femto-lora-openwrt-public-v1-sources.tar.gz}
tar --owner=0 --group=0 --numeric-owner -czf "$out" -C "$stage" .
sha256sum "$out"
