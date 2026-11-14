#!/usr/bin/env bash
set -euo pipefail
task_root=$(cd "$(dirname "$0")/.." && pwd)
cd "$task_root/openwrt"
expected=33063b4ccf00d39393796499b23df55187b192dc
actual=$(git rev-parse HEAD)
if [ "$actual" != "$expected" ]; then
  echo "Expected OpenWrt $expected, found $actual" >&2
  exit 1
fi
if git apply --reverse --check "$task_root/board/openwrt.patch" 2>/dev/null; then
  echo 'Board patch already applied.'
else
  git apply --check "$task_root/board/openwrt.patch"
  git apply --whitespace=nowarn "$task_root/board/openwrt.patch"
fi
"$task_root/tools/setup-feeds.sh"
cp "$task_root/board/config.build" .config
exec "$task_root/tools/build.sh" defconfig
