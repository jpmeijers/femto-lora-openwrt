# Continuing development

This is experimental, unsupported firmware. No known tested factory rollback
exists. Please keep that warning in forks, releases and installation guides.

Useful work includes documenting verified UART pad locations on each revision,
NAND/ECC fault testing, Wi-Fi calibration/performance, RF interoperability,
TX power calibration, more regional hardware profiles, and migration to a
maintained OpenWrt release. Preserve the original bootloader and calibration
partitions; do not infer safety from a single successful test unit.

Submit source patches with the build revision, hardware variant and a concise
test report. Distinguish RAM boot, NAND boot, normal reboot and power-cycle
testing. Do not claim a factory rollback procedure without demonstrating it.

## Privacy

Never commit device dumps, factory firmware, Wi-Fi credentials, LoRa keys,
real hardware MAC/EUI values, serial numbers, host private keys, personal
absolute paths, or label photographs. Redact logs before posting them.
Some `ubus` wireless status responses contain the saved Wi-Fi password.
Do not attach them unchanged.

The root `.gitignore` uses a public allowlist. Private research stays in
`private/`, `investigation/`, `backups/`, `logs/` and the ignored build/source
checkouts. Files there remain on disk; they are not publication artifacts.
`.gitignore` is not a secret scanner and does not remove already committed
history. Review `git diff --cached` and extracted images before each release.
