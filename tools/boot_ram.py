#!/usr/bin/env python3
"""Boot the uploaded RAM uImage and capture startup; stop a panic loop."""
import argparse
import time
from pathlib import Path
import serial

p = argparse.ArgumentParser()
p.add_argument('--log', required=True)
p.add_argument('--command', default='bootm a2000000')
p.add_argument('--seconds', type=float, default=40)
p.add_argument('--port', default='/dev/ttyUSB0', help='3.3 V TTL serial adapter')
args = p.parse_args()
s = serial.Serial(port=None, baudrate=57600, timeout=.1, exclusive=True)
s.port = args.port
s.dtr = False
s.rts = False
s.open()
s.write(args.command.encode() + b'\r')
data = bytearray()
activated = False
interrupted = False
end = time.monotonic() + args.seconds
while time.monotonic() < end:
    data.extend(s.read(16384))
    if b'Please press Enter to activate this console' in data and not activated:
        s.write(b'\r')
        activated = True
    if b'Kernel panic' in data and b'9: Load Boot Loader' in data and not interrupted:
        s.write(b'4')
        interrupted = True
s.close()
Path(args.log).parent.mkdir(parents=True, exist_ok=True)
Path(args.log).write_bytes(data)
print(f'Captured {len(data)} bytes; activated={activated}, panic={b"Kernel panic" in data}, bootloop_interrupted={interrupted}')
print(data.decode('utf8', 'replace')[-5000:])
