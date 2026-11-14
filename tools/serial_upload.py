#!/usr/bin/env python3
"""Bootstrap a CRC-checked RAM receiver through U-Boot's memory editor.

No NAND commands or persistent environment writes. Requires the bootloader
prompt at 57600 on entry. Leaves the uploaded image at 0xa2000000 and
restores 57600 on success. Run without an image for positive/negative tests.
"""
import argparse
import re
import struct
import time
import zlib
from pathlib import Path
import serial

root = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser()
p.add_argument('image', nargs='?')
p.add_argument('--log', default=str(root / 'logs/serial-upload.log'))
p.add_argument('--port', default='/dev/ttyUSB0', help='3.3 V TTL serial adapter')
args = p.parse_args()
log = bytearray()
s = serial.Serial(port=None, baudrate=57600, timeout=.05, exclusive=True)
s.port = args.port
s.dtr = False
s.rts = False
s.open()

def until(token, timeout=5):
    data = bytearray()
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        data.extend(s.read(s.in_waiting or 1))
        if token in data:
            log.extend(data)
            return bytes(data)
    log.extend(data)
    raise RuntimeError(f'Expected {token!r} at {s.baudrate} baud: {data[-200:]!r}')

def cmd(command, timeout=5):
    s.write(command.encode() + b'\r')
    return until(b'MT7620 # ', timeout)

def reg(address, value, baud=None):
    s.write(f'mm.l {address:x}\r'.encode())
    until(b'? ')
    s.write(f'{value:x}\r'.encode())
    s.flush()
    if baud:
        # USB flush is not UART shift-register drain. Let CR reach the old
        # speed first; ignore the prompt emitted during the speed change.
        time.sleep(.1)
        s.baudrate = baud
        s.reset_input_buffer()
    else:
        until(b'? ')
    s.write(b'q\r')
    until(b'MT7620 # ')

def baud_fast():
    reg(0xb0000c14, 0x83)
    reg(0xb0000c2c, 5, 500000)
    reg(0xb0000c14, 3)
    reg(0xb0000c10, 7)  # enable and clear RX/TX FIFOs

def baud_normal():
    reg(0xb0000c14, 0x83)
    reg(0xb0000c2c, 43, 57600)
    reg(0xb0000c14, 3)

def read_words(address, size):
    count = (size + 3) // 4
    data = cmd(f'md.l {address:x} {count:x}', max(5, count / 100))
    result = bytearray()
    for match in re.finditer(rb'(?m)^([0-9a-f]{8}):((?: [0-9a-f]{8}){1,4})', data.replace(b'\r', b'')):
        assert int(match[1], 16) == address + len(result)
        for word in match[2].split():
            result.extend(struct.pack('<I', int(word, 16)))
    assert len(result) == count * 4, (len(result), count)
    return bytes(result[:size])

def bootstrap():
    blob = (root / 'board/uart-loader.bin').read_bytes()
    words = blob + bytes((-len(blob)) % 4)
    s.write(b'mm.l a3000000\r')
    until(b'? ')
    for index, (value,) in enumerate(struct.iter_unpack('<I', words)):
        s.write(f'{value:08x}\r'.encode())
        prompt = until(b'? ')
        expected = f'{0xa3000000 + (index + 1) * 4:08x}:'.encode()
        assert expected in prompt, (expected, prompt)
    s.write(b'q\r')
    until(b'MT7620 # ')
    assert read_words(0xa3000000, len(blob)) == blob
    print(f'Bootstrap verified: {len(blob)} bytes', flush=True)

def transfer(data, corrupt_crc=False):
    assert 0 < len(data) <= 0x1000000
    s.write(b'go 83000000\r')
    until(b'FEMTO-READY\r\n')
    crc = zlib.crc32(data)
    header = struct.pack('<III', 0x314d5446, len(data), crc ^ int(corrupt_crc))
    start = time.monotonic()
    s.write(header)
    for offset in range(0, len(data), 16384):
        s.write(data[offset:offset + 16384])
    s.flush()
    output = until(b'MT7620 # ', 30)
    expected = b'FEMTO-BAD' if corrupt_crc else b'FEMTO-OK'
    assert expected in output, output
    seconds = time.monotonic() - start
    print(f'{len(data)} bytes in {seconds:.1f}s; CRC {"rejection" if corrupt_crc else "accepted"}', flush=True)
    if not corrupt_crc:
        assert read_words(0xa2000000, min(64, len(data))) == data[:64]
        if len(data) > 64:
            offset = (len(data) - 64) & ~3
            assert read_words(0xa2000000 + offset, len(data) - offset) == data[offset:]

try:
    cmd('q')  # An empty line repeats U-Boot's last command.
    baud_fast()
    bootstrap()
    if args.image:
        transfer(Path(args.image).read_bytes())
    else:
        data = bytes(range(256)) * 256
        transfer(data, corrupt_crc=True)
        transfer(data)
    baud_normal()
    print('Console restored to 57600 baud; flash unchanged.', flush=True)
finally:
    Path(args.log).parent.mkdir(parents=True, exist_ok=True)
    Path(args.log).write_bytes(log)
    s.close()
