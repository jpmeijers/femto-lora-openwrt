# Identity, region and EU transmit defaults

Only EU hardware is supported. Unsupported firmware, own risk, no known tested
factory rollback: the root README warnings still apply.

## Discovery order

`femto-board-info` reads the gateway's own MTD partitions using `O_RDONLY`:

1. It verifies the little-endian CRC32 over the first 4096-byte U-Boot
   environment in `Config` (CRC at bytes 0–3, data at bytes 4–4095).
2. If present, it decodes `lora_ee_cnt_0`, the vendor's **cached module EEPROM**.
   The first 8 bytes are the original LoRa EUI. Byte 8 contains a band code, and
   bytes 16–79 contain sixteen gain entries. The development cache has 126 bytes;
   the parser accepts bounded shorter records and only decodes available data.
3. Without a usable cached EUI, it reads six bytes at Factory offset 4: the
   factory Wi-Fi MAC. It inserts `FFFE` in the middle, sets the local U/L bit
   (`first_byte |= 0x02`) and retains unicast addressing. An already-local bit
   is **not toggled**. This produces a stable locally administered fallback.
4. An explicit Gateway EUI entered in LuCI overrides the automatic value.

There is no device EUI or MAC embedded in the downloadable image. Discovery
runs on your gateway, after boot. Factory data is not changed. The factory
Wi-Fi address is used rather than a virtual station/AP address which may vary
with configuration. A fallback is a new identity and may differ from the
original LoRa EUI; register the displayed value with your server. Duplicate
factory MACs or copied Factory partitions can still produce duplicate values.

Inserting `FFFE` is a common gateway convention. The local-bit setting here is
intentional and is not the IPv6 modified-EUI-64 bit-inversion algorithm; see
[RFC 4291 Appendix A](https://www.rfc-editor.org/rfc/rfc4291.html#appendix-A).

### Hardware EEPROM versus cache

The original vendor utility reads module EEPROM, and the original scripts
cache those bytes in manufacturing/bootloader settings. **This port reads
that CRC-protected cache, not the live EEPROM.** A native read through the
standard FPGA EEPROM target returned only erased bytes during investigation,
so a direct live EEPROM reader is not claimed. A cache can be missing or stale;
we do not synthesize a factory identity or write EEPROM to fill it in.

## Region

The LoRa radio chip alone cannot distinguish EU and US assemblies. Wi-Fi
country settings and the server hostname are not LoRa hardware identification.
Discovery combines cached `lora_country_code` with the module band byte:

- `EU` and/or band 1 indicate the supported EU case on the observed unit.
- Known non-EU country tags or band 0/2 are refused. Vendor production code uses
  band 0 for its 902-MHz setup and band 2 for 470 MHz; band 0 also covers other
  900-MHz provisioning, so this is **not** a complete US-versus-AS923 detector.
- Conflicting metadata is refused.
- If unknown, LuCI requires the operator to confirm an EU enclosure marking
  before the forwarder starts. Do not confirm EU for a US unit.

These are provisioning/cache heuristics, not an immutable RF-board identity.
We need a US unit's firmware/configuration evidence before implementing a US
profile. See [private dump and sanitized contribution instructions](DUMPING.md).

## Gain table evidence and defaults

We have one EU unit, not a set of factory calibration records from multiple
units. Therefore **we have no proof that every unit has different calibration,
and no proof that all units of this model are identical**.

What the original firmware does show:

- Its EEPROM utility has separate EUI, band, RX-offset and power-table fields.
- Startup compares EEPROM-derived power entries with configuration and imports
  the table if different.
- The packaged ROM table and this unit's active EU table differ in all 16 rows.
  That establishes support for variant/module-specific values; it does not
  establish unique calibration for each EU serial number.

The shipped EU reference table is the numeric active table recovered from the
EU development unit. It contains **no EUI, serial, MAC or credentials**. No
cross-unit calibration guarantee or independent power measurement is claimed.
When valid cached gain entries are available, they are preferred over the
reference table. An explicit advanced JSON plan overrides automatic table
selection. Gain fields are dig/PA/DAC/mixer settings and nominal RF power.
The cache uses half-dB labels; the upstream Semtech HAL ultimately represents
power labels as integer dBm, so half-step labels may be quantized.

**Downlinks are enabled by default**, using the cached table or EU reference
without requiring a custom plan. Users can explicitly disable them. The
forwarder itself remains off until configured, and non-EU/unknown-region
checks apply before startup. Configuration choices from older firmware are
preserved during upgrades; an existing disabled-TX setting is not overwritten.
