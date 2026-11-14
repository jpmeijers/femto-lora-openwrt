#!/usr/bin/env bash
set -euo pipefail
task_root=$(cd "$(dirname "$0")/.." && pwd)
# Optional local ncurses fallback; normal builds use host development packages.
export CPATH="$task_root/host-deps/usr/include${CPATH:+:$CPATH}"
export LIBRARY_PATH="$task_root/host-deps/usr/lib/x86_64-linux-gnu${LIBRARY_PATH:+:$LIBRARY_PATH}"
cd "$task_root/openwrt"
exec make "$@"
