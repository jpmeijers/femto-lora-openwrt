#!/usr/bin/env bash
set -euo pipefail
task_root=$(cd "$(dirname "$0")/.." && pwd)
cd "$task_root"
cross="$task_root/openwrt/staging_dir/toolchain-mipsel_24kc_gcc-12.3.0_musl/bin/mipsel-openwrt-linux-musl-"
"${cross}as" -EL -mips32r2 -o board/uart-loader.o tools/uart-loader.S
"${cross}ld" -EL -T tools/uart-loader.ld -Map board/uart-loader.map -o board/uart-loader.elf board/uart-loader.o
"${cross}objcopy" -O binary board/uart-loader.elf board/uart-loader.bin
"${cross}objdump" -d board/uart-loader.elf > board/uart-loader.dis
wc -c board/uart-loader.bin
