# Bluetooth Classic (BR/EDR) Sync

This document details the architecture, constraints, and operational steps for synchronizing Bluetooth Classic (BR/EDR) devices.

---

## 1. Fundamental Differences from BLE

Classic devices (keyboards, headsets, older mice) differ significantly from BLE peripherals:
1. **Link Key Storage**: Uses a 128-bit symmetric Link Key generated via Secure Simple Pairing (SSP) or legacy PIN.
2. **Single Bonding Slot**: Many low-cost BR/EDR HID peripherals maintain only one bonding entry in firmware. If paired fresh on Host A, Host B's prior bond is invalidated.
3. **No RPA Rotation**: Classic devices use fixed hardware BD_ADDR addresses, unlike BLE RPA rotating addresses.

---

## 2. Storage Mapping

### Windows Storage
Windows stores Classic Link Keys directly under the adapter key as a `REG_BINARY` value named after the lowercase device MAC (no subkey):
`HKLM\SYSTEM\CurrentControlSet\Services\BTHPORT\Parameters\Keys\<AdapterMAC>\<devicemac>` = `hex:11,22,33,44,...`

### Linux (BlueZ) Storage
BlueZ requires complete entries in `/var/lib/bluetooth/<AdapterMAC>/<DeviceMAC>/info`:
```ini
[General]
Name=Classic Keyboard
Class=0x002540
SupportedTechnologies=BR/EDR;
Trusted=true
Blocked=false
WakeAllowed=true

[LinkKey]
Key=11223344556677889900AABBCCDDEEFF
Type=4
PINLength=0

[DeviceID]
Source=2
Vendor=1234
Product=5678
Version=1
```

> [!IMPORTANT]
> If `Class`, `SupportedTechnologies`, or `[LinkKey]` are incomplete, BlueZ will fail with `br-connection-page-timeout` at the paging radio layer rather than an authentication error.

---

## 3. Operational Requirements

1. **Pre-flight Check**: Verify that the peripheral is powered on and not actively in a reconnection loop.
2. **Do Not Re-Pair**: After migration, do NOT press the device's physical pairing button; connect directly.
3. **Daemon Cycling**: Stop BlueZ service, clear stale state, write complete `info`, set permissions (`0600`), and restart service.
