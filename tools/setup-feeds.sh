#!/usr/bin/env bash
set -euo pipefail
task_root=$(cd "$(dirname "$0")/.." && pwd)
cd "$task_root/openwrt"
cat > feeds.conf <<'EOF'
src-git packages https://git.openwrt.org/feed/packages.git^f36055baca3ae8ba7f7bde3a9a6a6f3b1b9a82ea
src-git luci https://git.openwrt.org/project/luci.git^3d39e8c38cfa276d5cdfad7105dbf47933eaed4f
EOF
./scripts/feeds update packages luci
./scripts/feeds install luci luci-ssl libloragw libloragw-tests
cp "$task_root/board/lora-hal-half-duplex.patch" feeds/packages/net/lora-gateway-hal/patches/0004-half-duplex-register-reads.patch

if ! git -C feeds/packages apply --reverse --check "$task_root/board/lora-hal-package.patch" 2>/dev/null; then
 git -C feeds/packages apply --check "$task_root/board/lora-hal-package.patch"
 git -C feeds/packages apply "$task_root/board/lora-hal-package.patch"
fi
