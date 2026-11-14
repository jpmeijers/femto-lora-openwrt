# Read-only firmware dumps and US-model contributions

**Experimental and unsupported. No known tested factory rollback exists.**
A dump is evidence and a backup, not a proven restoration method. Do not flash
this EU firmware onto a US model. Read-only capture does not require erasing,
formatting, changing boot variables or writing an EEPROM.

## What would help US support

Keep full dumps private. Useful initial public evidence is:

- Model and regional variant stated as text, plus observed CPU/RAM/NAND layout.
- A redacted `/proc/mtd` listing, band/provisioning information, and the numeric
  factory TX gain table and channel-plan defaults.
- A sanitized `radio-profile.json` from the exporter below, when cache metadata
  is available. State whether it came from a US-labelled unit and stock firmware.

Do **not** attach whole NAND images, configuration archives, EEPROM blobs,
label photographs, MAC/EUI values, serial numbers, Wi-Fi passwords or LoRa keys
to a public issue. Ask the maintainer how to transfer original dumps privately
if raw evidence is needed. Do not assume a vendor's ROM directory is free of
identifiers or proprietary material merely because it is read-only.

## Option A: original firmware already has shell/SSH access

Use existing authorized access; do not guess default passwords. The host helper
uses SSH configuration/agent access in BatchMode and never stores passwords.
From this repository on your Linux computer:

```sh
python3 tools/dump-firmware.py --target root@GATEWAY --output private/us-stock-dump
```

Replace `GATEWAY` with the actual address. The output directory must be new.
The tool records `/proc/mtd` and streams **each listed MTD partition** directly
to gzip files on your computer. No full image needs to fit in gateway RAM.
Remote commands are only reads (`cat /dev/mtdN`). Native ECC handling applies;
an unreadable page may abort a partition. Failed/short transfers retain a
`.partial` file and do not produce a complete manifest.

Some vendor layouts include an overlapping whole-chip/ALL partition. Inspect
`proc-mtd.txt`; captures can duplicate data and require substantial disk space.
To capture selected indices instead, repeat `--partition`, for example:

```sh
python3 tools/dump-firmware.py --target root@GATEWAY \
  --output private/selected-stock-dump --partition 0 --partition 1
```

The indices above are examples, not a promise of names on stock firmware.
The final `manifest.json` gives sizes and SHA256 of **uncompressed** streams.
Verify that files decompress and that counts match the manifest. Preserve
failed captures separately; do not rename them to imply completeness.

These are data-only images. They do not include OOB/bad-block markers. Do not
blindly restore them using `mtd write`, especially across NAND bad blocks.

## Option B: UART and RAM recovery, without installing OpenWrt

Follow the README only through the critical backup and **RAM boot** steps.
Do not run `install-from-ram.sh`, `ubiformat`, `mtd write`, `nand write`, any
EEPROM setter, or `saveenv`. Verify CPU/RAM/NAND compatibility before booting
any image. A regional variant may differ; do not infer compatibility from its
model name alone. The RAM image starts with forwarding disabled; the region
checks also refuse known non-EU hardware.

The stock NAND layout is still present on storage even though the recovery
kernel presents the project's partition names. Give the computer its dedicated
static management address and establish SSH to the RAM system. Its temporary
SSH host key differs from the stock firmware; verify it through the local
console rather than disabling host-key checks indiscriminately.

The recovery image provides `rawdump`, which can read data plus OOB through
MEMREAD without writing flash. To stream data-only and raw+OOB captures:

```sh
python3 tools/dump-firmware.py --target root@192.168.88.10 \
  --output private/us-ram-nand-dump --raw-oob
```

This reads one eraseblock into a small exclusive `/tmp` file, streams it to the
host and removes it. A full-chip raw dump therefore does not need 512 MiB of RAM.
The raw tool verifies 2048-byte data/64-byte OOB geometry and does not skip bad
blocks. Capturing the full device can take a long time. If interrupted, inspect
and remove only `/tmp/femto-rawdump-chunk` before retrying with a fresh local
directory. Never delete or overwrite a device node to clear a temporary file.
Raw captures are page-data followed by OOB for each page; they are not normal
firmware upgrade images. These methods do not establish a factory rollback.

## Export a sanitized radio summary

On this project's running or RAM image:

```sh
mkdir -p private
ssh root@GATEWAY femto-board-info > private/board-info.json
python3 tools/export-radio-profile.py private/board-info.json > radio-profile.json
```

The **input is private** because it includes the gateway EUI. The exporter
whitelists only normalized region, band byte and numeric gain entries. It
excludes the EUI, all MACs, serials, keys and arbitrary extra fields. Review the
output before sharing. The helper reads the CRC-valid bootloader EEPROM cache;
it does not claim to have read the live module EEPROM. A missing cache is
reported as unknown, not silently treated as a US profile.
