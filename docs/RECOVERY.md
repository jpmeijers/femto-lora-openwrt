# Reset button and setup Wi-Fi

**Experimental and unsupported. Flashing remains at your own risk; no known
tested return to factory Gemtek firmware exists.** This procedure resets the
configuration of the installed OpenWrt image.

## Recover from a bad configuration

With the gateway powered on and fully booted:

1. Hold the rear reset pinhole button for about **10–12 seconds**, until the
   power indicator flashes amber, then release it.
2. Wait for the gateway to reboot. Configuration, administrator password,
   configured Wi-Fi, LoRa server/API key, SSH host keys and extra installed
   packages are cleared. Packages built into the image remain available.
3. Join the **open** Wi-Fi network named `Femto-Setup-…`. The suffix is generated
   from this gateway's hardware at runtime; no development-unit identifier is
   embedded in the image. A client should receive a `192.168.89.x` DHCP address.
4. Open **http://192.168.89.1/** and set an administrator password, then configure
   your network and LoRa connection in LuCI. Secure or disable the setup AP when
   finished. This setup network provides local management, without Internet
   forwarding; a phone may require “stay connected without Internet”.
5. Ethernet management remains **192.168.88.10/24**, with DHCP serving disabled
   on Ethernet. A computer directly attached there needs its own static address,
   such as `192.168.88.253/24`, with no gateway on that link.

A **quick tap** (less than a second) reboots without clearing settings. Holds
between one and nine seconds are ignored. The ten-second action is performed
on **release**, not simply on reaching the timeout. Test and use this sequence
on a running system; bootloader button combinations are not documented here.

The reset clears the writable OpenWrt overlay. The installed firmware and
protected bootloader/Factory/Config partitions are preserved, including the
original cached LoRa EUI/calibration and factory Wi-Fi MAC. A reset generates new
SSH host keys, so SSH clients will detect a changed host identity; verify the
new key through a trusted direct connection. Restoring a private OpenWrt backup
can restore the previous configuration and keys.

## First boot and upgrades

Fresh installations and full configuration resets create the setup AP above.
The fresh network configuration contains a one-time initialization marker.
Preserved upgrade configurations do not have it, so upgrades leave the
operator's Wi-Fi, DHCP, firewall and LoRa configuration intact and do not enable
an additional open AP. Keeping settings during a normal firmware upgrade is
therefore different from requesting a full configuration reset.

The setup AP uses a separate `br-setup` bridge/subnet and a dedicated firewall
zone. Its DHCP server does not serve Ethernet, and its traffic is not forwarded
to Ethernet or upstream networks. It uses 2.4 GHz channel 6 / HT20, with client
isolation enabled. It remains available until the operator secures/disables it
or replaces that Wi-Fi configuration; there is no automatic expiry during setup.

LoRa forwarding is disabled after a reset and no LNS key is configured. The
image's automatic EUI and EU gain-table discovery still work when the operator
configures forwarding again. Only EU LoRa hardware is supported.

## Hardware and implementation

The factory startup script runs `btnd reset 69`. GPIO69 was observed high at
rest and low while the physical button was pressed, then high on release.
The board device tree maps this input through `gpio-keys-polled` to the standard
OpenWrt reset event, with 20 ms polling and 60 ms debounce. The Femto handler
uses the standard OpenWrt overlay-reset tool, with an overlay-mounted guard;
it does not issue raw NAND writes or change boot variables. RAM recovery
cannot perform the long-press overlay reset.

## Regression checks

After preparing the matching source tree, these tests can use local scripts
via `--script PATH`, or test the installed version by omitting that argument:

```sh
python3 tests/test_reset.py --target root@GATEWAY
python3 tests/test_setup_defaults.py --target root@GATEWAY
```

The reset test substitutes erase/reboot commands with stubs. The defaults test
uses isolated UCI files and a stub Wi-Fi command. They do not reset the device,
change real radio settings or erase user configuration. They cover reset timing,
failed erase handling, RAM-root guards, preserving upgrades, isolated AP/DHCP
configuration, retrying unavailable radios and initialization idempotence.

On the EU development unit, the physical long hold produced amber feedback and
release cleared the overlay, regenerated SSH keys and brought up setup Wi-Fi.
A full reset/restore test verified real laptop association, a setup DHCP lease,
and the LuCI login page over Wi-Fi. Bootloader/Config/Factory hashes and the
factory EUI were unchanged. The private configuration backup was restored with
matching file hashes, the original SSH key returned, the setup AP disappeared,
and Basic Station reauthenticated to TTN. End-device LoRa RF traffic remains
outside this recovery test.
