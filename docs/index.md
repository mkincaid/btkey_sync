# btkey_sync Wiki

Welcome to the `btkey_sync` technical documentation wiki.

`btkey_sync` is a zero-dependency CLI tool written in Python 3.10+ to synchronize Bluetooth pairing and cryptographic bonding material (BLE LTK/EDIV/ERand/IRK and Classic BR/EDR Link Keys) across operating systems in dual-boot setups, partition migrations, or distinct physical machines.

---

## Documentation Index

| Topic | Document | Description |
|---|---|---|
| **Architecture** | [Architecture](file:///home/netss/Proyectos/btkey_sync/docs/architecture.md) | System components, data models, and backend contracts |
| **BLE Synchronization** | [BLE Sync](file:///home/netss/Proyectos/btkey_sync/docs/ble_sync.md) | BLE cryptographic material (LTK, EDIV, ERand, IRK) |
| **Classic Sync** | [Classic Sync](file:///home/netss/Proyectos/btkey_sync/docs/classic_sync.md) | Bluetooth Classic (BR/EDR) Link Key migration |
| **Device Cloning** | [Device Cloning](file:///home/netss/Proyectos/btkey_sync/docs/device_cloning.md) | Live & offline dual-boot cloning workflows |
| **Troubleshooting** | [Troubleshooting](file:///home/netss/Proyectos/btkey_sync/docs/troubleshooting.md) | Common errors, paging timeouts, and diagnostics |

---

## Key Design Principles

1. **Strict Line Limit (R14)**: All source and documentation files strictly adhere to a 200-line limit for maintainability and modularity.
2. **Deterministic Arithmetic**: Numeric conversions (hex ↔ decimal, little-endian ↔ big-endian) are always executed in code, never inferred mentally.
3. **No Network Elevation**: Windows SYSTEM elevation uses temporary scheduled tasks (`schtasks`), avoiding network/SMB/PsExec dependencies.
4. **Daemon Lifecycle**: BlueZ daemon is stopped and restarted cleanly during modifications to invalidate in-memory key caches.
5. **Reversibility**: Backups are automatically preserved before overwriting or removing any bonding folder.
