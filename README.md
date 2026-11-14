# femto-lora-openwrt

Experimental OpenWrt firmware for the **Gemtek WLRGFM-100 Femto LoRaWAN gateway**.
Includes LuCI web management for Ethernet, Wi-Fi and an SX1301 packet forwarder.

> [!WARNING]
> **FLASH ENTIRELY AT YOUR OWN RISK. THIS FIRMWARE IS EXPERIMENTAL AND UNSUPPORTED.**
> It can permanently brick your gateway, destroy data, or leave radios unusable.
> **There is no known, tested way to roll back to factory firmware. Treat this
> installation as permanent.** No factory firmware image or restoration service
> is provided. Backups do not guarantee that factory firmware can be restored.
> There is no warranty, support commitment, or affiliation with Gemtek or OpenWrt.

## Hardware and limitations

This port was developed on an **EU variant** with MT7620A, 256 MiB RAM,
512 MiB **parallel NAND**, and SX1301/SX1257 LoRa hardware. Other board revisions
and regional variants are untested. This is not a generic MT7620 image.
The base is a pinned OpenWrt 23.05 branch with Linux 5.15; it is not an official
supported OpenWrt device or a commitment to ongoing security maintenance.

Ethernet, persistent configuration, Wi-Fi station association/DHCP/DNS, Wi-Fi AP
beaconing/scanning, LoRa initialization, UDP gateway-server acknowledgments,
LuCI settings, web upgrades and normal reboot have been exercised on one unit.
Only **EU variants are supported**. The image recovers the LoRa EUI and gain
table from valid factory cache data when available. Otherwise it generates a
locally administered EUI from the factory Wi-Fi MAC and uses the included EU
reference gain table. Wi-Fi and forwarding start disabled; **downlinks default
to enabled** once forwarding is configured. Known non-EU units are refused;
unknown units require explicit EU confirmation in LuCI.
RF power, receiver sensitivity,
end-device RF round trips, other hardware revisions and cold-power recovery
are not comprehensively validated. The Wi-Fi driver can report an RXIQ
calibration warning while continuing to operate. See [board notes](docs/BOARD.md).

## Before you begin

You need a Linux computer, a verified **3.3 V TTL USB serial adapter**, access to
the board's UART, a reliable gateway power supply, and preferably Ethernet.
The enclosure label on the development unit specifies **5 V DC / 2 A**.
**The UART pad order is not documented here: identify and verify the pads on
YOUR board before connecting.** Do not copy a pinout from an unrelated Gemtek
router. Connect common ground and cross TX/RX. Do not connect the adapter's VCC,
RTS or DTR. Never use RS-232 voltage levels or 5 V UART signalling.

Before changing anything, use the original management interface to save the
LoRa gateway EUI, regional settings and calibrated TX gain table if available.
The enclosure MAC is not necessarily the original LoRa EUI. Keep backups and
identifiers private. See [identity, region and gain-table details](docs/IDENTITY-AND-REGION.md)
for discovery and fallback behavior. We have no proof that all units have
identical calibration or that each unit was calibrated individually.
For US-model investigation, follow the [read-only firmware dump instructions](docs/DUMPING.md);
do not install this EU firmware onto a US unit.

### 1. Get the project and firmware

```sh
git clone https://github.com/jpmeijers/femto-lora-openwrt.git
cd femto-lora-openwrt
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
mkdir -p logs
(cd firmware && sha256sum -c SHA256SUMS)
```

The `firmware/` directory contains a matching set of public images. Never mix
kernel and rootfs files from different builds. To build them yourself instead,
follow [BUILD.md](docs/BUILD.md). Set your adapter path:

```sh
export PORT=/dev/ttyUSB0
```

Use a terminal such as `picocom -b 57600 "$PORT"` to confirm readable console
output: **57600 baud, 8N1, no flow control**. Power-cycle the gateway and select
**menu option 4** to enter the existing U-Boot command line. Expect `MT7620 #`.
If the menu or hardware differs, stop. Do not flash the bootloader or use
`saveenv`. Close the terminal before running the Python tools.

### 2. Back up critical NAND contents

At the U-Boot prompt, with the terminal closed:

```sh
python3 tools/backup_uboot.py --port "$PORT" --output backups/this-gateway-critical
```

This read-only, resumable tool saves Bootloader, Config and Factory, including
OOB data. Use a **fresh output directory for each gateway**. It can take a long
time over serial. It does **not** back up the complete factory operating system
and does **not** establish a factory rollback procedure. Store complete backups
by whatever additional methods you have verified for your original firmware.
All `backups/` and `logs/` files are ignored by Git.

### 3. Boot OpenWrt in RAM first

This step transfers to RAM and does not write NAND:

```sh
python3 tools/serial_upload.py firmware/ram-recovery.bin --port "$PORT" --log logs/ram-upload.log
python3 tools/boot_ram.py --port "$PORT" --seconds 90 --log logs/ram-boot.log
```

The upload helper uses a supplied, source-built 507-byte RAM receiver, CRC32,
and temporary 500000-baud transfers, then restores 57600 baud. Do not interrupt
it. At the RAM recovery shell, verify the board name and partitions:

```sh
cat /tmp/sysinfo/board_name
cat /proc/mtd
```

The name must be `gemtek,wlrgfm-100`. In particular, `mtd3` must be `kernel`,
size `00800000`, and `mtd4` must be `ubi`, size `01600000`, both with erase size
`00020000`. See the full [partition map](docs/BOARD.md). **Stop on any mismatch.**
Do not proceed if the kernel panics, NAND geometry differs, or ECC read errors
are reported. Successful RAM boot is not proof that flash installation is safe.

### 4. Transfer the two flash payloads and installer

Close any interactive serial terminal. The RAM image contains `serial-file`:

```sh
python3 tools/linux_serial_transfer.py put firmware/kernel.bin /tmp/kernel.bin --port "$PORT" --log logs/kernel-upload.log
python3 tools/linux_serial_transfer.py put firmware/rootfs.ubi /tmp/rootfs.ubi --port "$PORT" --log logs/rootfs-upload.log
python3 tools/linux_serial_transfer.py put firmware/SHA256SUMS /tmp/SHA256SUMS --port "$PORT" --log logs/hashes-upload.log
python3 tools/linux_serial_transfer.py put tools/install-from-ram.sh /tmp/install-from-ram.sh --port "$PORT" --log logs/installer-upload.log
```

You can instead transfer the same files over a working Ethernet/SSH link.
The RAM LAN address is `192.168.88.10/24`; give your computer a different static
address in that subnet, with no gateway on this dedicated link. There is no
DHCP server by default. On a NetworkManager host you can create a dedicated
profile (replace the example interface with your wired adapter):

```sh
export ETH_IF=enp1s0
nmcli connection add type ethernet ifname "$ETH_IF" con-name femto-flash \
  ipv4.method manual ipv4.addresses 192.168.88.253/24 ipv4.never-default yes \
  ipv6.method disabled connection.autoconnect no
nmcli connection up femto-flash
```

If NetworkManager drops that profile when the gateway reboots, run
`nmcli connection up femto-flash` again. Check that the computer still has its
static IPv4 address before assuming the gateway failed to boot.
With recent `scp`, use legacy SCP mode (`scp -O`) or
pipe files over SSH; an SFTP server is not included.

### 5. Permanently replace firmware1

> [!CAUTION]
> **The following command erases and replaces the factory firmware1 slot.
> There is no known factory rollback. Do not remove power.**

Open the serial terminal again and run **in the RAM recovery shell**:

```sh
sh /tmp/install-from-ram.sh /tmp --erase-firmware1
```

The installer refuses a running NAND root filesystem or unexpected partition
layout, checks SHA256 values and image headers, formats **only** `mtd4` (`ubi`),
then writes **only** `mtd3` (`kernel`). It verifies the kernel readback and checks
that Bootloader/Config/Factory hashes did not change. It does not change the
saved U-Boot environment. These guards cannot make installation risk-free.
The helper wraps the previously exercised flash commands; a pristine-factory
installation on every hardware revision has not been tested.

If it fails, **stay in RAM recovery** and investigate. Do not try arbitrary
`mtd`, `nand write`, bootloader, whole-chip, or unrelated router images.
On success:

```sh
reboot
```

Allow at least a couple of minutes for the first boot. Key/certificate generation
and initial overlay setup are slow. Do not power-cycle a busy first boot.
From the console, `readlink /overlay/.fs_state` should eventually print `2`.

### 6. Configure through LuCI

Open **http://192.168.88.10/** over Ethernet. HTTPS is also available with a
self-signed certificate. Initially log in as **root**, with an empty password,
and set a password immediately under **System → Administration**.

- **Network → Interfaces:** Ethernet IP addressing, routes, DHCP client.
- **Network → Wireless:** configure your own SSID/security or join an upstream
  access point. The radio supports 2.4 GHz. For an Internet station connection,
  create/use a DHCP interface such as `wwan` in the appropriate firewall zone.
- **Network → DHCP and DNS:** DNS settings. DHCP serving on LAN is initially
  disabled; enable it under the LAN interface if you need client leases.
- **Services → LoRaWAN:** check the automatically discovered EUI, enter your
  network-server hostname and select the EU channel plan, then enable forwarding.
  Register the displayed EUI with your server; a manual EUI can override it.
  Downlinks default to enabled with the cached factory gain table or included
  EU reference table. Advanced JSON can override the plan and gain table.
- **System → System Log:** Wi-Fi, concentrator and packet-forwarder diagnostics.
  **System → System** provides clock/timezone settings and browser time sync.

Do not invent a gateway EUI from someone else's label or reuse a published EUI.
The default server `localhost` is a placeholder, not an Internet service.
The default upstream ACK timeout is 1000 ms to tolerate longer Internet paths.

## Experimental Basic Station

An optional SX1301 Basic Station package and LuCI protocol controls are available
in the development source. It supports direct TTN LNS connections over verified
TLS with a gateway API key. The `public-v2` firmware downloads contain UDP only;
see [Basic Station build, setup and validation notes](docs/BASIC-STATION.md)
before installing the experimental packages.

## Later OpenWrt upgrades

Once this port is already installed, use **System → Backup / Flash Firmware**
and upload **`firmware/sysupgrade.bin`** from the same project. Verify the
checksum and keep settings unless you deliberately want to reset them. Never
use the raw kernel, UBI or RAM image in that dialog; never force an image that
fails validation. Generic official OpenWrt images do not support this board.
Keeping settings retains your private configuration on the gateway; it does
not put that configuration into the public firmware files.

## Troubleshooting and development

- WPA handshake failures / `WRONG_KEY`: check the saved password and security
  mode first. Association without DHCP/default route/DNS is not Internet access.
- If the forwarder stopped after repeated DNS failures, restore connectivity
  then disable/re-enable it in LuCI. `PULL_ACK` and `PUSH_ACK` show server transport;
  they do not prove a real end-device RF round trip.
- Do not assume the stock bootloader's Ethernet/TFTP works. UART RAM loading
  was used during development; Linux Ethernet was tested separately.
- There is no guarantee of bootloader recovery after a failed flash. RAM rescue
  requires an intact, accessible bootloader and compatible hardware.

See [build instructions](docs/BUILD.md), [board/driver notes](docs/BOARD.md),
[contributing and privacy](docs/CONTRIBUTING.md), and [license/source notices](NOTICE.md).
