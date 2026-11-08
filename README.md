# postmarketOS on the OnePlus 7 (GM1903, guacamoleb)

Mainline Linux (postmarketOS edge, `linux-postmarketos-qcom-sm8150` 7.0) on the
OnePlus 7, used as a headless 24/7 server.

## Status

| Feature | Status |
| :--- | :--- |
| Boot (boot_a, rootfs on userdata) | Working |
| UFS storage, 6 GB RAM, 8 cores | Working |
| USB networking + SSH (`172.16.42.1`) | Working |
| Wi-Fi (ath10k_snoc, WCN3998), 2.4 and 5 GHz | Working (see firmware notes) |
| Charging (PM8150B SMB5) + fuel gauge | Working, capped at 4.10 V / 1 A |
| Reboot on unclean reset (TCSR dload-mode) | Working |
| Display, touch, audio, modem data, BT | Not tested / not configured |

## Contents

- `patches/0004-arm64-dts-qcom-add-oneplus-guacamoleb.patch` - device tree.
  The stock ABL only boots it with `qcom,msm-id = <339 0x20000>` and
  `qcom,board-id = <0 0>`, and only after `dtbo` is erased.
- `patches/0006-power-supply-qcom-smbx-smb5-limits-and-aicl.patch` - SMB5
  float voltage / fast-charge / ICL encodings (from the OnePlus 7 Pro and
  7T Pro bring-ups).
- `patches/device-oneplus-guacamoleb/` - pmaports device package.
- `tools/` - small stdlib-only helpers: `payload_extract.py` (A/B OTA
  payload.bin), `fdt_ids.py` / `fdt_dump.py` (inspect stock DTBs/DTBO),
  `sahara_reset.py` (reset a phone stuck in Qualcomm crash-dump mode,
  USB `05c6:900e`).

## Install outline

1. OxygenOS 12 refuses `fastboot oem unlock` ("Device cannot be unlocked for
   technical reason"). Roll back to OxygenOS 11 with the official rollback
   package and OnePlus' local-update APK, then unlock.
2. Add the patches to pmaports, `pmbootstrap init` (device
   `oneplus-guacamoleb`), `pmbootstrap install`.
3. `fastboot erase dtbo_a`, flash rootfs to `userdata` and the boot image to
   `boot_a` (`pmbootstrap flasher flash_rootfs` / `flash_kernel`).

## Wi-Fi firmware (not included, proprietary)

- `qcom/sm8150/oneplus7/modem.mdt` + `modem.bNN`: OxygenOS 11 `modem`
  partition (the OxygenOS 12 modem does not fit `mpss_mem`).
- `qcom/sm8150/oneplus7/wlanmdsp.mbn`: OxygenOS 12 `modem` partition
  (`WLAN.HL.3.0.c8-00232`). After a rollback it is still in `modem_b`.
- `ath10k/WCN3990/hw1.0/board-2.bin`: OnePlus `bdwlan.bin` from the same
  partition, packed as `bus=snoc,qmi-board-id=ff`.

The OxygenOS 11 `WLAN.HL.3.2.0` firmware with the generic linux-firmware
`board-2.bin` crashes the WLAN PD (`WCSS_WLAN1_GDSCR.PWR_ON`,
`SRPLL lock failed`) and takes the modem down.

## Credits

- [TheDankMan94/oneplus7pro-postmarketos](https://github.com/TheDankMan94/oneplus7pro-postmarketos)
- [yuweiyuan8/hotdog-linux-bringup](https://github.com/yuweiyuan8/hotdog-linux-bringup)
