#!/usr/bin/env python3
"""Run a command or collect output without toggling FTDI reset lines."""
import argparse
import time
from pathlib import Path
import serial

p = argparse.ArgumentParser()
p.add_argument('command', nargs='?')
p.add_argument('--seconds', type=float, default=3)
p.add_argument('--log', required=True)
p.add_argument('--until')
p.add_argument('--port', default='/dev/ttyUSB0')
args = p.parse_args()
s = serial.Serial(port=None, baudrate=57600, timeout=.1, exclusive=True)
s.port = args.port
s.dtr = False
s.rts = False
s.open()
if args.command:
    s.write(args.command.encode() + b'\r')
out = bytearray()
end = time.monotonic() + args.seconds
while time.monotonic() < end:
    data = s.read(16384)
    out.extend(data)
    if data:
        print(data.decode('utf8', 'replace'), end='', flush=True)
    if args.until and out.endswith(args.until.encode()):
        break
s.close()
Path(args.log).parent.mkdir(parents=True, exist_ok=True)
Path(args.log).write_bytes(out)
