# Building and reproducing the port

Read the README warnings first. This is an unsupported experimental port with
no known tested factory rollback. Build on a normal Linux filesystem as a
non-root user, with adequate disk space (allow tens of GB) and RAM.

## Dependencies

Use the prerequisites recommended by the pinned OpenWrt build system. On a
Debian/Ubuntu build host a typical starting point is:

```sh
sudo apt install build-essential clang flex bison g++ gawk gettext git \
  libncurses-dev libssl-dev python3 python3-venv python3-setuptools \
  rsync swig unzip zlib1g-dev file wget curl xz-utils
```

Package names vary by distribution. Let OpenWrt's prerequisite check identify
missing tools. The ignored `host-deps/` path is an optional local ncurses
fallback from development and is not required when host packages are installed.

## Pinned inputs

| Component | Revision |
|---|---|
| OpenWrt | `33063b4ccf00d39393796499b23df55187b192dc` |
| packages feed | `f36055baca3ae8ba7f7bde3a9a6a6f3b1b9a82ea` |
| LuCI feed | `3d39e8c38cfa276d5cdfad7105dbf47933eaed4f` |
| imported X-Wrt NAND driver | `372c1d30d0be58b70092710a5c298a321fb42318` |
| Semtech packet forwarder | `d0226eae6e7b6bbaec6117d0d2372bf17819c438` |
| Semtech HAL | `5.0.1`, as packaged by the pinned feed |

Recipes include download SHA256 values. Do not silently substitute a different
OpenWrt branch or feed version: kernel APIs, LuCI and image construction vary.

```sh
./tools/prepare.sh
./tools/build.sh -j4 download
./tools/build.sh -j4
./tools/build-uart-loader.sh
```

`prepare.sh` clones the pinned OpenWrt source into ignored `openwrt/`, applies
`board/openwrt.patch`, installs pinned feeds with the HAL patches, copies
`board/config.build`, and runs `defconfig`. It refuses a different source
revision. The build includes both normal and initramfs images.

Outputs are in `openwrt/bin/targets/ramips/mt7620/`. Public artifact names map to:

| Public file | OpenWrt output suffix |
|---|---|
| `ram-recovery.bin` | `-initramfs-kernel.bin` |
| `kernel.bin` | `-flash-kernel.bin` |
| `rootfs.ubi` | `-squashfs-rootfs.ubi` |
| `sysupgrade.bin` | `-squashfs-sysupgrade.bin` |

A combined factory image is also built for research; **do not use it as a
whole-chip image or in LuCI**. Only the matching sysupgrade file goes in LuCI.

## Editing the port

Edit the applied sources in `openwrt/`. Then use:

```sh
python3 tools/export-board.py
```

This exports tracked changes and an explicit list of custom source files into
`board/openwrt.patch`, saves the configuration, and reverse-checks the patch.
If you add a custom file outside the existing package, add it to the export
list. HAL feed changes are separate patches in `board/` and are applied by
`tools/setup-feeds.sh`. Keep the DTS/image-profile snapshots in sync.

After kernel configuration changes, stale module IPKs may require:

```sh
./tools/build.sh package/kernel/linux/clean package/kernel/gpio-button-hotplug/clean
./tools/build.sh -j4
```

## Source and binary publication

The repository contains the board modifications and exact build recipe, not a
copy of the proprietary factory root filesystem. `prepare.sh` obtains the
complete OpenWrt/feed source trees; `make download` obtains component archives.
Public releases can include a corresponding-source bundle made with
`tools/make-source-bundle.sh`, containing pristine pinned trees, downloaded
source archives and this project's committed patches and build instructions.
The individual upstream licenses remain applicable; see `NOTICE.md`.

Do not publish a filesystem copied from a running gateway. It contains private
configuration, generated host keys and identifiers. Use a clean build; inspect
both the staged Git files and extracted Squashfs before uploading binaries.
The image has no hardcoded gateway EUI and uses generic build user/host metadata.
It includes a numeric EU reference TX table. Factory identity and calibration
cache are read on the user's own gateway at runtime; see `IDENTITY-AND-REGION.md`.
Host metadata-parser checks: `python3 tests/test_board_info.py` (after prepare).

## Optional Basic Station package

See [BASIC-STATION.md](BASIC-STATION.md) for the SX1301 package, TTN LNS setup
and test limits. The configuration selects `femto-basicstation=y`, embedding it in the
firmware. Change to `=m` if you only want an optional IPK. Use a fresh
OpenWrt preparation directory when changing between project revisions; the
apply helper deliberately rejects a partially applied older board patch.

The committed `firmware/` binaries are the `public-v3` release artifacts.
For their exact corresponding board source/configuration, check out Git tag
`public-v3` before preparing the build. Development-source changes do not
retroactively change those published binary artifacts.
