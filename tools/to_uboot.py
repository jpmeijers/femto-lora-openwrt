#!/usr/bin/env python3
"""Reboot recovery Linux and stop at the vendor U-Boot prompt."""
import argparse
import time
from pathlib import Path
import serial

p = argparse.ArgumentParser()
p.add_argument('--log', required=True)
p.add_argument('--port', default='/dev/ttyUSB0', help='3.3 V TTL serial adapter')
args = p.parse_args()
s = serial.Serial(port=None, baudrate=57600, timeout=.1, exclusive=True)
s.port = args.port
s.dtr = False
s.rts = False
s.open()
s.write(b'reboot\r')
data = bytearray()
sent = False
end = time.monotonic() + 40
while time.monotonic() < end:
    data.extend(s.read(s.in_waiting or 1))
    if b'9: Load Boot Loader' in data and not sent:
        time.sleep(.1)
        s.write(b'4')
        sent = True
    if sent and data.endswith(b'MT7620 # '):
        break
else:
    raise RuntimeError('Failed to stop at U-Boot')
s.close()
Path(args.log).parent.mkdir(parents=True, exist_ok=True)
Path(args.log).write_bytes(data)
print('Stopped at U-Boot; saved environment unchanged.')
