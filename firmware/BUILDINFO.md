# Public build

Build identifier: `public-v4`, prepared 2026-11-15.
OpenWrt 23.05 branch / Linux 5.15.211, MIPS little-endian 24kc.
Exact upstream revisions and regeneration commands: `docs/BUILD.md`.
Matching configuration, board patch and HAL patches are at Git tag `public-v4`.
Package versions are in `packages.manifest`; artifact hashes in `SHA256SUMS`.

This image adds eight GPIO LED outputs (four green/amber icon pairs), automatic
Internet/Wi-Fi/LoRa readiness indicators, OpenWrt boot indications, and System →
Gateway LEDs controls in LuCI. Native Basic Station connection/radio events and
validated UDP acknowledgments provide credential-free RAM health markers.
See `docs/LEDS.md` for exact meanings and detection limits.

Basic Station 2.0.6 with its private SX1301 HAL/Femto SPI fixes and Semtech UDP
are included. New installations have Wi-Fi and forwarding disabled, UDP selected
and no LNS API key. Upgrades preserve the chosen protocol and credentials.
No device EUI, MAC, Wi-Fi password, API key or generated SSH private key is
embedded. Build user/host metadata is generic.

Factory-cache EUI discovery, locally administered Wi-Fi-MAC fallback, cached/EU
reference TX gains and enabled downlink defaults are retained. EU hardware only.

**Experimental and unsupported. Flash at your own risk. No known tested factory
rollback exists.** Evidence comes from one EU unit. End-device RF round trips,
measured RF power/sensitivity, Class B and other hardware variants remain
unverified. CUPS is not configured.

## Validation

The three green status LED GPIOs were physically confirmed against the enclosure.
Synthetic on-device policy tests cover live/dead processes, owned/unrelated TCP
sockets, radio-ready flags, fresh/stale UDP ACKs, Wi-Fi states, disabled functions
and manual LED control. Image uImage CRCs, embedded RAM CPIO privacy and exact
UBI-to-Squashfs contents were checked. Public files and the extracted rootfs are
scanned against known private identifiers and credentials.

The first-install helper rejects NAND-root execution before writes. Its complete
factory-to-RAM automated installation remains untested on pristine factory
firmware; the underlying manual write sequence was used during bring-up.

The exact public-v4 image booted through NAND sysupgrade with private Wi-Fi/LoRa
configuration and SSH key hashes unchanged. All four green GPIO outputs were
verified. Stopping the enabled forwarder produced amber; disabling LoRa turned
both LoRa outputs off. Basic Station reauthenticated to TTN and the indicator
returned to green. The automatic service, LuCI configuration tracking and
on-device isolated policy tests passed on the installed image.
A native UDP test with a local acknowledgment peer also produced a green LoRa
indicator; authenticated Basic Station was restored afterward without changing
saved configuration.
