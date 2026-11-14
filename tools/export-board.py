#!/usr/bin/env python3
"""Export the reproducible board port, excluding generated build files."""
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
tree = root / 'openwrt'
patch = subprocess.check_output(['git', 'diff', '--binary'], cwd=tree)
files = [
    'target/linux/ramips/dts/mt7620a_gemtek_wlrgfm-100.dts',
    'target/linux/ramips/files/drivers/mtd/maps/ralink_nand.c',
    'target/linux/ramips/files/drivers/mtd/maps/ralink_nand.h',
    'target/linux/ramips/patches-5.15/961-mtd-ralink-add-mt7620-nand-driver.patch',
    'target/linux/ramips/patches-5.15/962-spi-rt2880-board-rx-edge.patch',
    'files/etc/config/network',
    'package/utils/femto-serial-file/Makefile',
    'package/utils/femto-serial-file/src/serial-file.c',
    'package/utils/femto-serial-file/src/rawdump.c',
]
files += [str(p.relative_to(tree)) for p in sorted((tree / 'package/utils/femto-lorawan').rglob('*')) if p.is_file()]
for name in files:
    result = subprocess.run(['git', 'diff', '--no-index', '--binary', '/dev/null', name], cwd=tree, stdout=subprocess.PIPE)
    assert result.returncode == 1
    patch += result.stdout
(root / 'board/openwrt.patch').write_bytes(patch)
(root / 'board/config.build').write_bytes((tree / '.config').read_bytes())
subprocess.run(['git', 'apply', '--reverse', '--check', str(root / 'board/openwrt.patch')], cwd=tree, check=True)
print(f'Exported and checked {len(patch)}-byte board patch')
