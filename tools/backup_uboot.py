#!/usr/bin/env python3
"""Read critical NAND pages including OOB via vendor U-Boot, resumably."""
import argparse
import hashlib
import json
import re
import time
from pathlib import Path
import serial

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--port', default='/dev/ttyUSB0')
p.add_argument('--output', type=Path, default=Path('backups/uboot-critical'))
args = p.parse_args()
root = args.output
root.mkdir(parents=True, exist_ok=True)
s = serial.Serial(port=None, baudrate=57600, timeout=.1, exclusive=True)
s.port = args.port
s.dtr = False
s.rts = False
s.open()
for page in range(0x140000 // 2048):
    dest = root / f'page-{page:06x}.bin'
    if dest.exists():
        assert dest.stat().st_size == 2112
        continue
    s.write(f'nand page {page:x}\r'.encode())
    out = bytearray()
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        out.extend(s.read(8192))
        if out.endswith(b'MT7620 # '):
            break
    else:
        raise RuntimeError(f'Timed out at page {page:x}: {out[-100:]!r}')
    (root / f'page-{page:06x}.txt').write_bytes(out)
    assert f'page 0x{page:x}:'.encode() in out
    values = []
    for line in bytes(out).replace(b'\r', b'').splitlines():
        if re.fullmatch(rb'(?:[0-9a-fA-F]{2} ){31}[0-9a-fA-F]{2}\s*', line):
            values.extend(bytes.fromhex(line.decode()))
    assert len(values) == 2112, (page, len(values))
    dest.write_bytes(bytes(values))
    if page % 32 == 0:
        print(f'Backed up {page + 1}/640 pages', flush=True)
s.close()
manifest = {}
for name, start, length in [('Bootloader', 0, 0x80000), ('Config', 0x80000, 0x80000), ('Factory', 0x100000, 0x40000)]:
    pages = [ (root / f'page-{n:06x}.bin').read_bytes()
              for n in range(start // 2048, (start + length) // 2048) ]
    for suffix, data in [('raw-oob', b''.join(pages)), ('data', b''.join(p[:2048] for p in pages))]:
        filename = f'{name}-{suffix}.bin'
        (root / filename).write_bytes(data)
        manifest[filename] = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
(root / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print('Critical NAND backup complete, with OOB and original page transcripts.', flush=True)
