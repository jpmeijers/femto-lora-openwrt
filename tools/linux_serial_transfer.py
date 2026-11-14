#!/usr/bin/env python3
"""Transfer a regular file through serial-file in recovery Linux."""
import argparse
import hashlib
import shlex
import struct
import time
import zlib
from pathlib import Path
import serial

p = argparse.ArgumentParser()
p.add_argument('mode', choices=['put', 'get'])
p.add_argument('local')
p.add_argument('remote')
p.add_argument('--log', required=True)
p.add_argument('--port', default='/dev/ttyUSB0', help='3.3 V TTL serial adapter')
args = p.parse_args()
local = Path(args.local)
if args.mode == 'get' and local.exists():
    raise SystemExit('Refusing to overwrite the local backup')
payload = local.read_bytes() if args.mode == 'put' else None
s = serial.Serial(port=None, baudrate=57600, timeout=.1, exclusive=True)
s.port = args.port
s.dtr = False
s.rts = False
s.open()
log = bytearray()

def exact(n):
    data = bytearray()
    deadline = time.monotonic() + 15
    while len(data) < n:
        chunk = s.read(n - len(data))
        if chunk:
            data.extend(chunk)
            deadline = time.monotonic() + 15
        elif time.monotonic() > deadline:
            raise TimeoutError('Serial file transfer stalled')
    return bytes(data)

def until(token):
    data = bytearray()
    while not data.endswith(token):
        data.extend(exact(1))
    log.extend(data)
    return bytes(data)

try:
    command = f'dmesg -n 1; serial-file {args.mode} {shlex.quote(args.remote)} /dev/ttyS0\r'
    s.write(command.encode())
    s.flush()
    time.sleep(.3)
    s.baudrate = 500000
    time.sleep(.1)
    s.reset_input_buffer()
    s.write(b'U')
    until(b'FEMTO-LINUX-READY\r\n')
    start = time.monotonic()
    if payload is not None:
        s.write(struct.pack('<III', 0x314d5446, len(payload), zlib.crc32(payload)))
        for offset in range(0, len(payload), 16384):
            s.write(payload[offset:offset + 16384])
        s.flush()
    else:
        magic, length, expected = struct.unpack('<III', exact(12))
        assert magic == 0x314d5446 and 0 < length <= 512 * 1024 * 1024
        remaining, crc = length, 0
        with local.open('xb') as output:
            while remaining:
                chunk = exact(min(16384, remaining))
                output.write(chunk)
                crc = zlib.crc32(chunk, crc)
                remaining -= len(chunk)
        assert crc == expected, 'Backup CRC mismatch; retain file for diagnosis'
        s.write(b'\x06')
    until(b'FEMTO-LINUX-OK\r\n')
    s.baudrate = 57600
    time.sleep(.4)
    s.write(b"printf '\\nFEMTO-SHELL\\n'\r")
    until(b'\r\nFEMTO-SHELL\r\n')
    size = len(payload) if payload is not None else length
    print(f'{size} bytes transferred, CRC verified, {time.monotonic() - start:.1f}s')
    print('SHA256:', hashlib.sha256(local.read_bytes()).hexdigest())
finally:
    Path(args.log).parent.mkdir(parents=True, exist_ok=True)
    Path(args.log).write_bytes(log)
    s.close()
