# Experimental firmware artifacts

**UNSUPPORTED. FLASH AT YOUR OWN RISK. NO KNOWN TESTED FACTORY ROLLBACK.**
Read the root README before doing anything with these files.

`ram-recovery.bin` boots in RAM; it is not an upgrade image.
`kernel.bin` and `rootfs.ubi` are the matching first-install payloads.
`sysupgrade.bin` is only for later upgrades from this port through LuCI.
`SHA256SUMS` verifies this exact set; do not mix builds.
No per-device identifier, Wi-Fi password or private key is embedded. A numeric
EU reference TX table is included. Identity and gain cache are read from your
own hardware at runtime. Only EU models are supported; see docs/IDENTITY-AND-REGION.md.
