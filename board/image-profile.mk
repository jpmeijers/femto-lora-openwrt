define Device/gemtek_wlrgfm-100
  SOC := mt7620a
  DEVICE_VENDOR := Gemtek
  DEVICE_MODEL := WLRGFM-100
  IMAGE_SIZE := 30720k
  BLOCKSIZE := 128k
  PAGESIZE := 2048
  DEVICE_PACKAGES := kmod-usb2 kmod-usb-ohci kmod-spi-dev luci luci-ssl dnsmasq femto-lorawan
  KERNEL_SIZE := 8192k
  UBINIZE_OPTS := -E 5
  IMAGES := factory.bin rootfs.ubi sysupgrade.bin
  IMAGE/factory.bin := append-kernel | pad-to $$(KERNEL_SIZE) | append-ubi | check-size
  ARTIFACTS := flash-kernel.bin
  ARTIFACT/flash-kernel.bin := append-kernel
  IMAGE/rootfs.ubi := append-ubi | check-size 22528k
  IMAGE/sysupgrade.bin := sysupgrade-tar | append-metadata
endef
TARGET_DEVICES += gemtek_wlrgfm-100
