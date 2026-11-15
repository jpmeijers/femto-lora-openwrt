# Enclosure indicators

The four icons, left to right, are **power, Internet, Wi-Fi, LoRa**. Each has
green and amber outputs. The mapping comes from the original firmware's actual
LED lookup function (its introductory comments describe a different layout).
Turning on the three green status outputs was physically confirmed on the EU
development gateway. No enclosure photograph or device identifiers are published.

| Icon | Green GPIO | Amber GPIO | Normal automatic behavior |
|---|---:|---:|---|
| Power | 66 | 70 | Green after boot; boot/failsafe/upgrade use OpenWrt status indications |
| Internet | 67 | 68 | Green with a ready LoRa server connection, or a successful configured probe; otherwise amber |
| Wi-Fi | 8 | 10 | Green for station association or an active AP, amber while enabled but not ready, off when disabled |
| LoRa | 9 | 7 | Green for a ready radio and server connection, amber while enabled but not ready, off when disabled |

All outputs are **active low**. GPIO 7–10 use the UARTF pin group, configured
as GPIO. The management console is on the separate UART-lite pins and is not
changed. LoRa power GPIO30 and reset GPIO60 are not LED outputs.

## LoRa health

Basic Station writes credential-free RAM markers when its authenticated LNS
WebSocket opens/closes and when radio startup succeeds. The monitor requires
both markers to belong to the same live Station process, a radio-start marker
from the current connection, and an established TCP socket owned by that
process. A running process alone is insufficient. Green indicates protocol/radio
readiness, not a measured RF transmission or proof of end-device coverage.
A silent network failure may take time for TCP/Station to detect.

The UDP forwarder writes a radio-start marker and separate markers only for
validated PUSH_ACK/PULL_ACK messages. Green requires a matching live forwarder
and a server acknowledgment within the last 90 seconds. Without acknowledgments
it becomes amber even if the process is still running.

The monitor polls every five seconds. When no ready LoRa connection is available,
the Internet indicator can use one ICMP ping at most every 30 seconds, by default
to `1.1.1.1`. This is a reachability check, not a guarantee that every Internet
service works; networks that block ICMP can show amber despite having Internet.
A successful LoRa server connection also satisfies this indicator without probes.

## Web controls and custom behavior

**System → Gateway LEDs** enables/disables automatic indicators and changes the
probe host (IPv4 address or hostname). Clear the probe host to rely only on the
LoRa server connection for the Internet indicator. Disabling automatic control
leaves the last displayed states; configure custom triggers under
**System → LED Configuration**. Re-enabling automatic control takes ownership
of the six Internet/Wi-Fi/LoRa outputs again. Power remains an OpenWrt boot LED.

Linux exposes `green:power`, `amber:power`, `green:internet`, `amber:internet`,
`green:wifi`, `amber:wifi`, `green:lora` and `amber:lora` in `/sys/class/leds`.
Status markers and cached probe results are in RAM, not written repeatedly to NAND.
The markers contain process IDs, uptime and readiness only, without EUI or keys.

## Validation

The isolated test `python3 tests/test_leds.py --target root@GATEWAY` checks
ready/disconnected radios, owned versus unrelated TCP sockets, dead processes,
fresh versus stale UDP acknowledgments, enabled/disconnected/disabled Wi-Fi,
and disabled automatic control. It redirects all LED/proc/marker paths into a
temporary fixture directory; it does not change the real LEDs or radio service.

The exact public-v4 firmware booted on the development unit with existing network
and LoRa configuration preserved. All four green GPIO outputs were checked.
A stopped-but-enabled forwarder produced amber, disabled LoRa produced off, and
restarting Basic Station restored green after authenticated TTN configuration
and radio startup. Automatic service startup and web configuration tracking
were verified; isolated policy tests also passed on the installed firmware.

A local UDP peer also returned real protocol acknowledgments to the native
packet forwarder. Its matching radio/ACK markers turned LoRa green. Basic
Station was then restored and reconnected, with saved configuration unchanged.
