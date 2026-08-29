# Architecture & Design

This document details the software architecture, data contracts, and backend abstraction layers in `btkey_sync`.

---

## 1. High-Level Architecture

The project decouples user interface workflows, serialization formats, and OS-specific storage mechanisms:

```
                  ┌──────────────────────┐
                  │    CLI / TUI Layer   │
                  │ (cli.py, actions_*)  │
                  └──────────┬───────────┘
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
   ┌─────────────────┐               ┌─────────────────┐
   │ Models & Schema │               │ Exporters &     │
   │   (models.py)   │               │ Importers       │
   └────────┬────────┘               └────────┬────────┘
            │                                 │
            └────────────────┬────────────────┘
                             │
                             ▼
                 ┌───────────────────────┐
                 │    BluetoothBackend   │
                 │   (backends/base.py)  │
                 └───────────┬───────────┘
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
┌───────────────────────┐         ┌───────────────────────┐
│ LinuxBluetoothBackend │         │WindowsBluetoothBackend│
│ (/var/lib/bluetooth)  │         │ (HKLM Services\BTH..) │
└───────────────────────┘         └───────────────────────┘
```

---

## 2. Core Models (`models.py`)

- **`BondKey`**: Represents BLE bonding material. All numeric fields (`ediv`, `erand`) are stored in decimal internally.
  - `adapter_mac`: Local controller MAC address (`AA:BB:CC:DD:EE:FF`).
  - `device_mac`: Remote device MAC address.
  - `ltk_hex`: 128-bit Long Term Key (32 hex characters).
  - `ediv`: Encrypted Diversifier (16-bit unsigned integer).
  - `erand`: Encrypted Randomizer (64-bit unsigned integer).
  - `irk_hex`: Identity Resolving Key (for RPA address resolution).
- **`LinkKeyBond`**: Represents Bluetooth Classic (BR/EDR) bonding material.
  - `link_key_hex`: 128-bit Link Key (32 hex characters).
  - `key_type`: SSP key derivation type (e.g. `4` for unauthenticated combination key).
  - `pin_length`: PIN length (`0` for SSP).
  - `device_class`: Device class hexadecimal string (e.g. `0x002540` for HID keyboard).
- **`DiscoveredDevice`**: Metadata describing locally paired devices during discovery and export.

---

## 3. Backend Contract (`backends/base.py`)

The abstract `BluetoothBackend` enforces standard operations:
- `check_prerequisites() -> List[str]`: Evaluates environment permissions and prerequisites.
- `list_devices() -> List[DiscoveredDevice]`: Lists local paired devices.
- `extract_bond_key(device) -> BondKey`: Reads bonding keys from the host.
- `import_bond_key(bond, target_device_mac) -> Path`: Injects bonding keys into local host storage.
- `restart_bluetooth_stack()`: Invalidates daemon in-memory cache.
- `remove_bond_key(adapter_mac, device_mac, remove_backups)`: Removes local bonding configuration safely.

---

## 4. Module Limits (Rule R14)

Every Python source file strictly contains fewer than 200 lines. Features are split modularly into specialized orchestrators (`actions_clone.py`, `actions_classic.py`, `actions_verify.py`, etc.).
