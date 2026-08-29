# BLE Synchronization (Bluetooth Low Energy)

This document explains how Bluetooth Low Energy (BLE) bonding material is structured, extracted, and synchronized across operating systems.

---

## 1. BLE Cryptographic Material

BLE Security Manager (SM) bonding creates several key elements:
- **LTK (Long Term Key)**: 128-bit key used to encrypt connection data.
- **EDIV (Encrypted Diversifier)**: 16-bit integer used by the peripheral to identify the LTK.
- **ERand (Encrypted Randomizer)**: 64-bit random number used with EDIV.
- **IRK (Identity Resolving Key)**: 128-bit key used to resolve Resolvable Private Addresses (RPA).

---

## 2. Storage Mapping

### Windows Storage
Windows stores BLE keys in the SYSTEM registry hive under:
`HKLM\SYSTEM\CurrentControlSet\Services\BTHPORT\Parameters\Keys\<AdapterMAC>\<DeviceMAC>`

- `LTK`: `REG_BINARY` (16 bytes, raw or byte-swapped depending on OS export).
- `EDiv`: `REG_DWORD` (stored as little-endian 32-bit integer).
- `ERand`: `REG_QWORD` (stored as little-endian 64-bit integer).
- `IRK`: `REG_BINARY` (16 bytes).

### Linux (BlueZ) Storage
BlueZ stores BLE keys in `/var/lib/bluetooth/<AdapterMAC>/<DeviceMAC>/info`:
```ini
[General]
Name=MX Master 3S
AddressType=static
SupportedTechnologies=LE;
Trusted=true

[LongTermKey]
Key=11223344556677889900AABBCCDDEEFF
Authenticated=0
EncSize=16
EDiv=12345
Rand=9876543210987654321

[IdentityResolvingKey]
Key=FFEEDDCCBBAA00998877665544332211
EncSize=16
```

---

## 3. Endianness & Numeric Conversions

`btkey_sync` enforces executable conversions:
- `EDiv` in Windows `.reg` files is hexadecimal (`dword:00003039`) converted to decimal (`12345`) for BlueZ.
- `ERand` in Windows `.reg` files is hexadecimal (`hex(b):...` or `qword:...`) converted to decimal for BlueZ.
- `BondKey` in `models.py` maintains `ediv` and `erand` as native decimal integers.
