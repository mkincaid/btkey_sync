"""
actions_clone.py

Unified, simplified cloning workflow for BLE, Classic, and Dual-Mode devices.
Maintains 200-line file limit (AGENTS.md R14).
"""

from __future__ import annotations

from pathlib import Path
from platform_detect import OSKind
import tui_helpers as tui
import actions_common as common
from backends import LinuxBluetoothBackend
from models import BondKey, LinkKeyBond
from actions_verify import force_push_sync, verify_and_connect
from actions_clone_loader import UnifiedDevice, load_windows_devices, load_linux_devices


def _resolve_target_adapter(backend: LinuxBluetoothBackend, src_adapter_mac: str) -> str | None:
    """Finds or prompts for the local Linux Bluetooth adapter destination."""
    local_adapters = backend._list_adapters()
    if not local_adapters:
        tui.err("No local Bluetooth adapters found under /var/lib/bluetooth.")
        return None

    if src_adapter_mac in local_adapters:
        return src_adapter_mac
    if len(local_adapters) == 1:
        target = local_adapters[0]
        if target.upper() != src_adapter_mac.upper():
            tui.info(f"Using local adapter: {tui.bold(target)} {tui.dim(f'(source was {src_adapter_mac})')}")
        return target

    print(f"\n  {tui.bold('Select local destination adapter:')}")
    for i, ad in enumerate(local_adapters, 1):
        print(f"    [{i}] {ad}")
    choice = tui.ask("Adapter number", default="1")
    if choice.isdigit() and 1 <= int(choice) <= len(local_adapters):
        return local_adapters[int(choice) - 1]
    return local_adapters[0]


def _write_cloned_keys(backend: LinuxBluetoothBackend, chosen_dev: UnifiedDevice, target_mac: str, target_adapter: str, target_dir: Path) -> None:
    """Writes Classic and/or BLE keys to BlueZ directory for cloned device."""
    if chosen_dev.classic_bond:
        cb = chosen_dev.classic_bond
        bond_clone = LinkKeyBond(
            adapter_mac=target_adapter,
            device_mac=target_mac,
            link_key_hex=cb.link_key_hex,
            key_type=cb.key_type,
            pin_length=cb.pin_length,
            device_class=cb.device_class,
            device_name=chosen_dev.name,
            device_id=cb.device_id,
            service_uuids=cb.service_uuids,
            source_os=cb.source_os,
        )
        backend.write_classic_info(bond_clone, target_dir)

    if chosen_dev.ble_bond:
        bb = chosen_dev.ble_bond
        bond_clone = BondKey(
            adapter_mac=target_adapter,
            device_mac=target_mac,
            ltk_hex=bb.ltk_hex,
            ediv=bb.ediv,
            erand=bb.erand,
            auth_req=bb.auth_req,
            device_name=chosen_dev.name,
            source_os=bb.source_os,
            irk_hex=bb.irk_hex,
            address_type=bb.address_type,
            is_le=bb.is_le,
        )
        backend.import_bond_key(bond_clone, target_device_mac=target_mac)

    backend.set_info_permissions(target_dir / "info")


def run_unified_clone_flow() -> None:
    """Clones a device from source (Windows/Linux) automatically handling BLE/Classic/Both."""
    tui.header("Clone Device — Step 1: System detection")
    env, backend = common.detect_and_validate()
    if env.os_kind != OSKind.LINUX or not isinstance(backend, LinuxBluetoothBackend):
        tui.err("Cloning is only supported on Linux.")
        return

    tui.header("Clone Device — Step 2: Choose source")
    source_os, win_mount = common.prompt_source_os(env.os_kind)
    devices = load_windows_devices(win_mount) if source_os == OSKind.WINDOWS else load_linux_devices(backend)

    if not devices:
        tui.warn("No bonded devices found on the source.")
        return

    tui.header("Clone Device — Step 3: Choose device")
    for i, dev in enumerate(devices, 1):
        print(f"  [{i}]  {dev.summary()}")
    print()

    choice = tui.ask("Device number [q to cancel]", default="q")
    if choice.lower() == "q" or not choice.isdigit() or not (1 <= int(choice) <= len(devices)):
        tui.info("Cancelled.")
        return

    chosen_dev = devices[int(choice) - 1]

    if chosen_dev.classic_bond:
        tui.header("Classic/Dual-Mode Pre-flight Warning")
        tui.warn("This device contains Bluetooth Classic bonding keys.")
        tui.warn("Classic/Dual-Mode devices usually support only ONE active bonding slot.")
        tui.info("Make sure the device is powered on, and do NOT put it in pairing mode during/after clone.")
        if tui.ask("Type 'yes' to proceed", default="").lower() != "yes":
            tui.info("Aborted.")
            return

    tui.header("Clone Device — Step 4: Destination MAC & Adapter")
    target_mac = tui.ask("Destination MAC (Enter to keep original)", default=chosen_dev.mac)

    bond = chosen_dev.ble_bond or chosen_dev.classic_bond
    if not bond:
        tui.err("No bonding keys found for this device.")
        return

    src_adapter = bond.adapter_mac
    target_adapter = _resolve_target_adapter(backend, src_adapter)
    if not target_adapter:
        return

    with tui.Spinner(f"Checking if {target_mac} is currently connected…"):
        is_connected = backend.check_active_link(target_mac)
    if is_connected:
        tui.warn(f"Device {target_mac} is currently connected!")
        if tui.ask("Proceed anyway? [y/N]", default="N").strip().lower() != "y":
            tui.info("Aborted.")
            return

    target_dir = backend.bluetooth_dir / target_adapter / target_mac
    if target_dir.exists():
        tui.warn(f"Existing bonding folder found: {target_dir}")
        if tui.ask("Over-write existing bonding? [y/N]", default="N").strip().lower() != "y":
            tui.info("Aborted.")
            return

    tui.header("Clone Device — Step 5: Write and restart Bluetooth")
    with tui.Spinner("Stopping Bluetooth service…"):
        backend.stop_bluetooth()

    if target_dir.exists():
        backend.remove_bond_key(target_adapter, target_mac)

    backend.disable_discovery_if_active()

    with tui.Spinner(f"Writing bonding info for {target_mac}…"):
        _write_cloned_keys(backend, chosen_dev, target_mac, target_adapter, target_dir)

    with tui.Spinner("Starting Bluetooth service…"):
        backend.start_bluetooth()

    tui.ok("Bonding successfully cloned!")
    if chosen_dev.classic_bond:
        tui.warn_classic_post_import(target_mac)

    force_push_sync(backend, target_mac)
