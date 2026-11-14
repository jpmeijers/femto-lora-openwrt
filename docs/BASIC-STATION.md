# Experimental Basic Station for TTN

**EU only. Unsupported, at your own risk. No known tested factory rollback.**
This is an experimental package integration; the `public-v2` downloadable
firmware still contains the Semtech UDP forwarder only. Existing UDP settings
remain the default. The two protocols share one concentrator and must not run
at the same time.

## What is implemented

- Semtech Basic Station 2.0.6, pinned upstream release source/hash, built for
  Linux MIPS little-endian and **SX1301**, not SX1302 or USB PicoCell.
- A private, statically linked LoRa HAL 5.0.1 with upstream Station patches and
  the Femto half-duplex SPI register-read fix. The working UDP HAL is unchanged.
  The existing kernel RX-edge quirk remains necessary. SPI requests 4 MHz.
- The same automatic EUI, EU-region checks, cached/reference TX gains and
  optional manual EUI as UDP. `euiprefix: ::0` prevents upstream Station from
  expanding an already complete EUI that happens to begin with zero bytes.
- Direct **LNS over WSS** with system CA verification and gateway bearer token.
  Credentials are generated into a private RAM directory. Persistent API keys
  are kept in the root-only LoRa UCI configuration and included in private
  OpenWrt configuration backups. Never share those backups.
- The LNS supplies channel frequencies; local RF type, clock source, RSSI
  offset, antenna gain and TX calibration remain board configuration.
- GPIO reset before reconfiguration; the default upstream 200 ms reset timeout
  is extended to 5 seconds for the vendor's three-second power/reset sequence.
- LuCI protocol selection, LNS endpoint and masked API-key input. One procd
  service owns whichever protocol is selected. CUPS is not configured.

The pinned OpenWrt feed already has a package named `basicstation`, but its
CMake configuration selects SX1302/USB and is unsuitable for this board. Use
**`femto-basicstation`**, together with the updated `femto-lorawan` package.

## Build and install on this port

Check out the development revision containing this document and follow
[BUILD.md](BUILD.md) to prepare the pinned OpenWrt tree, then:

```sh
./tools/build.sh defconfig
./tools/build.sh package/femto-basicstation/compile -j4
./tools/build.sh package/femto-lorawan/compile -j4
```

`board/config.build` selects Station as an optional module package (`=m`), so
it is built as an IPK and is not included in the default firmware rootfs.
To include it in a newly built firmware, select `CONFIG_PACKAGE_femto-basicstation=y`
in OpenWrt configuration before running the full build. Merely installing the
package does not select Station or replace your configured UDP connection.

On a gateway **already running this project's matching OpenWrt port**, install
both IPKs from `openwrt/bin/packages/mipsel_24kc/base/` with `opkg install` after
copying them to `/tmp/`. Install `femto-lorawan` release 5 or later together with
`femto-basicstation`. Do not install these packages into stock firmware or an
unrelated OpenWrt build. Save a private configuration backup first. Dependency
resolution must succeed; never bypass it with force flags. The package uses the
image's mbedTLS and CA bundle. Reload LuCI after installing the new controls.

## Connect to The Things Network

1. In the TTN Console for your cluster, create/select your gateway with the
   **same EUI shown in LuCI**. Choose the correct **EU863–870 frequency plan**.
   Server-side plan selection controls the channel layout used by Station.
2. Create a **gateway API key** with **Link as Gateway to a Gateway Server for
   traffic exchange** rights. A user/application key or CUPS-only key is not a
   substitute. Keep it private; do not paste it into GitHub issues or logs.
3. In **Services → LoRaWAN**, select **Basic Station**. For the Europe cluster
   use `wss://eu1.cloud.thethings.network:8887`. Other clusters use their own
   hostname. This integration accepts a WSS hostname with optional port and no
   URL path. Use the cluster where your gateway is registered.
4. Enter the API key alone in **LNS API key**. The firmware creates the required
   `Authorization: Bearer …` line with CRLF termination. Do not add that prefix
   in the LuCI field. Enable forwarding and Save & Apply.
5. Ensure Wi-Fi or Ethernet provides Internet, DNS and outbound TCP **8887**.
   Ensure system date/time is correct for certificate validation; configure NTP
   or sync browser time under **System → System** if needed.
6. Check **System → System Log** for TLS, router discovery, `router_config` and
   `Concentrator started`, then check TTN gateway live data. Never disable TLS
   verification to work around a wrong clock, CA bundle or hostname.

Switch the protocol back to **Semtech UDP**, preserving its hostname and ports,
then Save & Apply to return to the previous connection. The token can be cleared
when no longer needed. Updating packages preserves existing configuration;
therefore older configurations may not contain the new options until saved.

## CUPS and limits

Direct LNS is sufficient to exchange LoRaWAN traffic. CUPS can later provision
LNS credentials and manage updates, but is not part of these LuCI controls.
No CUPS-based firmware installation or remote firmware update workflow is claimed.
The current investigation does not establish end-device RF downlink timing,
measured output power, Class B operation, or support for other regional hardware.

## Sources

- [Semtech Basic Station source and build overview](https://github.com/lorabasics/basicstation/tree/v2.0.6).
- [Semtech SX1301 reference-design configuration](https://doc.sm.tc/station/gw_v1.5.html).
- [TTN / The Things Stack LNS setup and API-key rights](https://www.thethingsindustries.com/docs/hardware/gateways/concepts/lora-basics-station/lns/).
- [TTN / The Things Stack server addresses](https://www.thethingsindustries.com/docs/concepts/server-addresses/).

## Validation status

On the EU development unit:

- Both packages cross-compiled and installed; existing Wi-Fi, LoRa configuration
  and SSH key hashes were preserved. UDP forwarding was restored after tests.
- An isolated TLS LNS fixture verified the bearer header and discovery exchange,
  delivered an EU channel plan, received Station's `version` message, and the
  real SX1301 concentrator started successfully using automatic cached gains.
  The configured factory EUI was preserved exactly.
- The gateway reached TTN Europe over verified TLS and received `Unauthorized`
  for a deliberate test-only token. This establishes DNS/TCP/TLS/LNS reachability,
  independently of credentials. A subsequent test with an operator-provided
  temporary gateway key **authenticated successfully**, received TTN's EU868
  channel plan and started the concentrator. The temporary key was removed from
  the gateway after testing; no real key is included in this project.
- Isolated configuration tests rejected missing credentials, plaintext endpoints,
  and unsupported/conflicting region metadata. They verified CRLF bearer-file
  formatting, private token-file permissions, gain conversion, exact EUI use,
  reset timeout, and LNS-controlled channel frequencies.

Run the synthetic metadata tests on the build host with
`python3 tests/test_board_info.py`. On an updated development gateway with SSH
key/agent access, run `python3 tests/test_station_config.py --target root@GATEWAY`.
The latter uses a temporary configuration and synthetic identity; it does not
change persistent settings or run the radio. Authenticated TTN discovery and configuration passed. End-device uplink/downlink
traffic and RF behavior remain unverified.
