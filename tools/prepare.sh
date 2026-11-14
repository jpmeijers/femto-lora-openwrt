#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-only
set -euo pipefail
task_root=$(cd "$(dirname "$0")/.." && pwd)
cd "$task_root"
revision=33063b4ccf00d39393796499b23df55187b192dc
if [ ! -d openwrt/.git ]; then
 git clone --no-checkout https://github.com/openwrt/openwrt.git openwrt
 git -C openwrt checkout --detach "$revision"
fi
exec "$task_root/tools/apply-board.sh"
