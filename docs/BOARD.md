# Board and implementation notes

**Experimental and unsupported. Installation is at your own risk. No known,
tested factory firmware rollback exists.** See the README before flashing.

The tested EU hardware is a Gemtek WLRGFM-100, MT7620A at 580 MHz, 256 MiB DDR2,
512 MiB parallel NAND with 2048-byte pages, 64-byte OOB and 128-KiB eraseblocks.
Do not assume another regional variant or revision has these characteristics.
The enclosure label cannot verify the NAND geometry or UART pad order.

| MTD | Label | Physical start | Size | Access |
|---|---|---:|---:|---|
| 0 | Bootloader | `0x00000000` | `0x00080000` | read-only |
| 1 | Config | `0x00080000` | `0x00080000` | read-only |
| 2 | Factory | `0x00100000` | `0x00040000` | read-only |
| 3 | kernel | `0x00140000` | `0x00800000` | writable |
| 4 | ubi | `0x00940000` | `0x01600000` | writable |
| 5 | firmware2 | `0x01f40000` | `0x01e00000` | read-only |
| 6 | stock_rootfs_data | `0x03d40000` | `0x01400000` | read-only |
| 7 | data | `0x05140000` | `0x14a00000` | read-only |
| 8 | reserved | `0x19b40000` | `0x064c0000` | read-only |

Only the former firmware1 slot is repurposed. Retaining the other areas is not
a tested factory rollback path. The normal image is a uImage kernel plus UBI
Squashfs and UBIFS overlay. Default UBI bad-block reservation is conservative
and leaves only about 5 MiB of writable overlay despite the large NAND chip.

## NAND driver

The X-Wrt MT7620 parallel-NAND driver was ported to Linux 5.15. Changes include
512-MiB geometry, serialized bad-block marker reads, first/second-page checks,
ECC-enabled normal reads, raw reads only on explicit request, corrected/failure
reporting, and avoiding forced good/bad marker overwrites. Writes must be page
aligned. Data and raw+OOB reads were compared locally with bootloader captures;
writes, kernel readback, UBI/UBIFS and persistent reboot were exercised. ECC
fault injection and long-term wear testing have not been performed.

`rawdump` uses read-only MEMREAD to capture data+OOB. Standard `nanddump -n`
may fail because the driver intentionally does not expose raw OOB writes.
Raw page+OOB captures are **not** files to feed to `mtd write`.

## Ethernet and Wi-Fi

All physical switch ports are initially LAN, with VLANs disabled; Ethernet is
bridged for Wi-Fi AP support. The switch port wired to the enclosure Ethernet
connector negotiated 100baseT full-duplex. Default management is the private
example subnet in the README, without a DHCP server or upstream route.

Factory Wi-Fi calibration is read from this gateway's own Factory partition.
Ethernet derives its address from that partition too; none is embedded in the
published source or firmware. rt2800 can emit an RXIQ calibration warning and
fall back to default corrections. AP beaconing, passive receive scanning and
station IP traffic worked; sensitivity, throughput, and all security/AP modes
have not been characterized. PCIe and SD remain disabled. USB controllers
initialize, but attached USB peripherals are not validated.

## LoRa SPI

The tested assembly uses SX1301, SX1257 radios and FPGA version 33. GPIO30 is
module power and GPIO60 is reset, based on the vendor startup scripts. Reset
is low→high→low; power cycling is high→low→high. Only module0 is supported.

The MT7620 SPI controller is half-duplex. The HAL patch splits simple register
reads into command/write and data/read transfers with chip select retained.
Stock OpenWrt forces mode0 to mode3. That setting lost one MCU program byte per
SPI burst on this hardware. Idle-low clock with independent RX/TX falling-edge
settings gave exact 8192-byte firmware readback and successful MCU calibration.
DTS property `ralink,rx-falling-edge` enables that controller quirk only here;
other boards keep existing behavior. At the chosen clock the configuration
register is `0x135`; the SPI parent clock was approximately 193 MHz.

FPGA notch-filter programming may produce a warning. TX behavior and RF power
are not comprehensively validated. Only EU hardware is supported. The EU868
template includes the development unit's numeric reference gain table;
valid factory-cached entries take precedence. Automatic EUI discovery, region
checks and evidence about calibration are documented in
[IDENTITY-AND-REGION.md](IDENTITY-AND-REGION.md). Never write calibration EEPROM
during normal installation or operation.

## UART loader

57600, 8N1, no flow control. The small MIPS receiver lives at `0x83000000` and
receives through an uncached alias into physical RAM `0x02000000`, bounded to
16 MiB. Temporary UART divisor5 gives 500000 baud; divisor43 restores 57600.
Header/CRC32 and RAM readback catch transfer corruption. All changes are
volatile; no `saveenv` is used. UART upload does not require bootloader Ethernet.
An empty U-Boot line repeats its last command: the tools use explicit commands.

Board pad numbering has not been published/verified for all revisions. The
project does not supply a guessed UART pinout or photographs with device IDs.
Community background: [original TTN discussion](https://www.thethingsnetwork.org/forum/t/gemtek-indoor-femto-lorawan-gateway-anyone-else-using-one/11106).
