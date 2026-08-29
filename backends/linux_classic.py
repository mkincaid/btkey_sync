"""
backends/linux_classic.py

Discrete Classic (BR/EDR) backend operations for LinuxBluetoothBackend.
Respects 200-line limit (AGENTS.md R14).
"""

from __future__ import annotations

import configparser
from pathlib import Path
from typing import Optional

from models import DiscoveredDevice, LinkKeyBond
from .linux_common import (
    set_info_permissions,
    stop_bluetooth_daemon as stop_bluetooth,
    start_bluetooth_daemon as start_bluetooth,
    check_active_link,
    disable_discovery_if_active,
)


def extract_classic_bond(bluetooth_dir: Path, device: DiscoveredDevice) -> LinkKeyBond:
    """Read [LinkKey], [General], and [DeviceID] from BlueZ info file."""
    info_path = Path(device.raw_source_path)
    if not info_path.exists():
        raise FileNotFoundError(f"info file not found: {info_path}")

    cfg = configparser.ConfigParser()
    cfg.optionxform = str
    cfg.read(info_path)

    if "LinkKey" not in cfg:
        raise ValueError(f"No [LinkKey] section in {info_path}")

    lk = cfg["LinkKey"]
    link_key_hex = lk.get("Key", "")
    key_type = int(lk.get("Type", "0"))
    pin_length = int(lk.get("PINLength", "0"))

    gen = cfg["General"] if "General" in cfg else {}
    device_class = gen.get("Class", "")
    device_name = gen.get("Name", device.device_name)
    raw_uuids = gen.get("Services", "")
    service_uuids = [u for u in raw_uuids.split(";") if u.strip()]

    device_id: Optional[dict] = None
    if "DeviceID" in cfg:
        did = cfg["DeviceID"]
        device_id = {
            "source": did.get("Source", ""),
            "vendor": did.get("Vendor", ""),
            "product": did.get("Product", ""),
            "version": did.get("Version", ""),
        }

    return LinkKeyBond(
        adapter_mac=device.adapter_mac,
        device_mac=device.device_mac,
        link_key_hex=link_key_hex,
        key_type=key_type,
        pin_length=pin_length,
        device_class=device_class,
        device_name=device_name,
        device_id=device_id,
        service_uuids=service_uuids,
        source_os="linux",
    )


def write_classic_info(bond: LinkKeyBond, target_dir: Path) -> Path:
    """Write a complete BlueZ info file for a Classic bond (RC3)."""
    target_dir.mkdir(parents=True, exist_ok=True)
    info_path = target_dir / "info"

    cfg = configparser.ConfigParser()
    cfg.optionxform = str
    if info_path.exists():
        cfg.read(info_path)

    if "General" not in cfg:
        cfg["General"] = {}

    cfg["General"]["Name"] = bond.device_name or cfg["General"].get("Name", "Imported Device")
    cfg["General"]["Class"] = bond.device_class or cfg["General"].get("Class", "0x000000")
    cfg["General"]["Trusted"] = "true"
    cfg["General"]["Blocked"] = "false"
    cfg["General"]["CablePairing"] = "false"
    cfg["General"]["WakeAllowed"] = "true"
    cfg["General"]["Services"] = ";".join(bond.service_uuids) or cfg["General"].get("Services", "")

    techs = cfg["General"].get("SupportedTechnologies", "")
    if "LE;" in techs or "LongTermKey" in cfg:
        cfg["General"]["SupportedTechnologies"] = "BR/EDR;LE;"
    else:
        cfg["General"]["SupportedTechnologies"] = "BR/EDR;"

    cfg["LinkKey"] = {
        "Key": bond.link_key_hex,
        "Type": str(bond.key_type),
        "PINLength": str(bond.pin_length),
    }

    if bond.device_id:
        cfg["DeviceID"] = {
            "Source": str(bond.device_id.get("source", "")),
            "Vendor": str(bond.device_id.get("vendor", "")),
            "Product": str(bond.device_id.get("product", "")),
            "Version": str(bond.device_id.get("version", "")),
        }

    with open(info_path, "w") as f:
        cfg.write(f, space_around_delimiters=False)

    return info_path
