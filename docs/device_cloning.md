# Device Cloning & Dual-Boot Setup

This guide details cloning Bluetooth bonds from a mounted Windows partition or another Linux installation into the local Linux BlueZ environment.

---

## 1. Prerequisites

### Tools
- **Linux**: BlueZ (`bluetoothctl`, `systemctl`), Python 3.10+, `sudo` permissions.
- **Offline Windows reading**: `chntpw` package providing the `reged` utility to inspect mounted offline `SYSTEM` registry hives without booting Windows.

```bash
# Debian / Ubuntu / Mint
sudo apt install chntpw bluetooth
```

---

## 2. Cloning Workflow

The unified clone wizard (`actions_clone.py`) handles BLE, Classic, and Dual-Mode devices:

1. **Detection**: Detects local controller adapters under `/var/lib/bluetooth`.
2. **Source Selection**:
   - **Mounted Windows Partition**: Reads `Windows/System32/config/SYSTEM` offline using `reged`.
   - **Local Linux**: Inspects `/var/lib/bluetooth`.
3. **Device Selection**: Discovers all bonded devices, displaying device name, MAC, and transport type (`BLE`, `Classic`, or both).
4. **Target Adapter & MAC Mapping**: Maps to local Bluetooth controller and handles destination MAC remapping if needed.
5. **Atomic Write & Restart**:
   - Stops Bluetooth service (`systemctl stop bluetooth`).
   - Removes old target bonding directory with backup preservation.
   - Writes new `info` file with complete fields and `0600` permissions.
   - Restarts Bluetooth service (`systemctl start bluetooth`).
6. **Connection Verification**: Automatically verifies and attempts a test connection using `bluetoothctl`.

---

## 3. CLI Usage

```bash
# Run the interactive clone wizard
sudo btkey-sync clone

# Or execute directly via Python module
sudo python3 -m btkey_sync clone
```

> [!TIP]
> Make sure Windows Fast Startup is disabled in Windows (`powercfg /h off`) so the NTFS partition can be mounted safely in read-only or read-write mode.
