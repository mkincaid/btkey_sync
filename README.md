# btkey-sync

[![PyPI version](https://img.shields.io/pypi/v/btkey-sync.svg)](https://pypi.org/project/btkey-sync/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Synchronize Bluetooth pairing and cryptographic bonding keys (**BLE** and **Classic BR/EDR**) between operating systems in dual-boot setups (Windows & Linux) or across partitions and physical machines — **without having to re-pair devices on every reboot**.

---

## Why This Exists

Bluetooth peripherals (keyboards, mice, headsets) generate cryptographic keys during pairing. Dual-booting causes devices to fail on OS switches because each OS stores independent keys:

| Feature | Windows | Linux (BlueZ) |
|---|---|---|
| **Storage Location** | `HKLM\SYSTEM\...\BTHPORT\Parameters\Keys` | `/var/lib/bluetooth/<adapter>/<device>/info` |
| **Required Privileges** | SYSTEM account (automated via scheduled task) | `root` (`sudo`) |
| **Numeric Formats** | Hexadecimal (`dword`, `qword`, `hex`) | Decimal (`EDiv`, `Rand`) |
| **Daemon Reload** | Immediate | Requires `systemctl restart bluetooth` |

`btkey-sync` automates extracting, converting, importing, and validating keys across systems.

---

## Installation

### From PyPI

```bash
pip install btkey-sync
```

*(Or via `pipx install btkey-sync` for isolated CLI environments)*

### From Source

```bash
git clone https://github.com/netssv/btkey_sync.git
cd btkey_sync
pip install .
```

### Optional Dependencies (Linux Offline Windows Reading)
To clone directly from a mounted Windows partition on Linux without booting Windows:
```bash
sudo apt install chntpw bluetooth   # Debian/Ubuntu/Mint
sudo dnf install chntpw bluez       # Fedora/RHEL
sudo pacman -S chntpw bluez-utils   # Arch Linux
```

---

## Usage

### 1. Interactive TUI Menu (Recommended)

Run the command with elevated privileges:

**Linux:**
```bash
sudo btkey-sync
```
*(If run as normal user, `btkey-sync` will offer to re-launch with `sudo` automatically).*

**Windows (PowerShell / Command Prompt as Administrator):**
```powershell
btkey-sync
```

The menu provides:
- **[1] Clone Device**: Directly sync BLE, Classic, or Dual-Mode devices from a mounted Windows partition (`/mnt/windows`) or local installation.
- **[2] Export Key to File**: Export device pairing data to `.reg` + `.json` sidecar files.
- **[3] Import Key from File**: Load a `.reg` file and inject keys into the host Bluetooth stack.
- **[4] Force Push Sync**: Clear daemon caches, restart BlueZ, set trust, and reconnect.
- **[5] Remove Device**: Delete bonding for a device cleanly with automatic backup.
- **[6] Show Keys**: Inspect all locally stored bonding keys and parameters.
- **[7] Device Help & Advice**: Guidance on BLE vs. Classic single-slot devices.

---

### 2. Direct CLI Flags

```bash
# Non-interactive import of an exported .reg file
sudo btkey-sync --import exports/aabbccddeeff__windows__20260829.reg

# Force reload BlueZ stack, trust, and reconnect to a specific MAC
sudo btkey-sync --push-sync AA:BB:CC:DD:EE:FF
```

---

## Dual-Boot Migration Workflows

### Method A: Offline Cloning on Linux (Fastest)
1. Pair device in **Windows**.
2. Boot into **Linux** and mount your Windows partition (e.g. at `/mnt/windows`).
3. Run `sudo btkey-sync` and select **Option 1 (Clone Device)**.
4. Select the detected Windows partition. `btkey-sync` reads the keys offline and sets up BlueZ automatically.

### Method B: Export / Import via `.reg` File
1. Pair device on **Source OS** (e.g. Windows).
2. Run `btkey-sync` → **Option 2 (Export)** to generate a `.reg` file in `exports/`.
3. Copy the `.reg` file to the **Destination OS** (via USB drive or shared partition).
4. On destination, run `sudo btkey-sync` → **Option 3 (Import)**.

---

## Documentation Wiki

Detailed guides are available in the [docs/](docs/index.md) directory:
- [Architecture & Design](docs/architecture.md)
- [BLE Synchronization (LTK/EDIV/ERand/IRK)](docs/ble_sync.md)
- [Classic BR/EDR Sync (Link Keys)](docs/classic_sync.md)
- [Dual-Boot Cloning Guide](docs/device_cloning.md)
- [Troubleshooting & Diagnostics](docs/troubleshooting.md)

---

## Testing

```bash
python3 tests/test_parsing.py
```

## License

MIT License. See [LICENSE](LICENSE) for details.

<!-- GitHub integration check: safe to close this PR without merging. -->
