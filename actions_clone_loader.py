"""
actions_clone_loader.py

Device aggregation and loader helpers for cloning workflows.
Respects 200-line limit (AGENTS.md R14).
"""

from __future__ import annotations

from pathlib import Path
from models import BondKey, LinkKeyBond
import tui_helpers as tui
from backends.offline_windows import extract_bt_keys_from_hive, reged_available
from backends.offline_windows_classic import extract_classic_bt_keys_from_hive


class UnifiedDevice:
    """Represents a device that can have BLE keys, Classic keys, or both."""

    def __init__(self, mac: str, name: str | None = None):
        self.mac = mac
        self.name = name or "Unknown Device"
        self.ble_bond: BondKey | None = None
        self.classic_bond: LinkKeyBond | None = None

    def summary(self) -> str:
        types = []
        if self.ble_bond:
            types.append("BLE")
        if self.classic_bond:
            types.append("Classic")
        return f"{tui.bold(self.name)} ({'/'.join(types)}) [{tui.dim(self.mac)}]"


def load_windows_devices(win_mount: Path | None) -> list[UnifiedDevice]:
    """Load both Classic and BLE keys from Windows partition and merge them."""
    from actions_common import find_windows_system_hive

    if not reged_available():
        tui.err("reged (chntpw) is not installed. Install chntpw to read offline hives.")
        return []

    hive = find_windows_system_hive(win_mount)
    if not hive:
        tui.err("Could not find Windows SYSTEM hive in mounted path.")
        return []

    tui.ok(f"Hive: {tui.dim(str(hive))}")
    ble_bonds: list[BondKey] = []
    classic_bonds: list[LinkKeyBond] = []

    with tui.Spinner("Reading Windows registry hive…"):
        try:
            ble_bonds = extract_bt_keys_from_hive(hive)
        except Exception as exc:
            tui.warn(f"Could not extract BLE keys: {exc}")

        try:
            classic_bonds = extract_classic_bt_keys_from_hive(hive)
        except Exception as exc:
            tui.warn(f"Could not extract Classic keys: {exc}")

    devices_map: dict[str, UnifiedDevice] = {}
    for b in ble_bonds:
        mac = b.device_mac.upper()
        if mac not in devices_map:
            devices_map[mac] = UnifiedDevice(mac, b.device_name)
        devices_map[mac].ble_bond = b

    for cb in classic_bonds:
        mac = cb.device_mac.upper()
        if mac not in devices_map:
            devices_map[mac] = UnifiedDevice(mac, cb.device_name)
        devices_map[mac].classic_bond = cb
        if cb.device_name and devices_map[mac].name == "Unknown Device":
            devices_map[mac].name = cb.device_name

    return list(devices_map.values())


def load_linux_devices(backend) -> list[UnifiedDevice]:
    """Scan local Linux BlueZ directory for bonded devices."""
    devices = backend.list_devices()
    devices_map: dict[str, UnifiedDevice] = {}
    for d in devices:
        mac = d.device_mac.upper()
        dev = UnifiedDevice(mac, d.device_name)

        if d.has_ltk:
            try:
                dev.ble_bond = backend.extract_bond_key(d)
            except Exception:
                pass

        try:
            dev.classic_bond = backend.extract_classic_bond(d)
        except Exception:
            pass

        if dev.ble_bond or dev.classic_bond:
            devices_map[mac] = dev

    return list(devices_map.values())
