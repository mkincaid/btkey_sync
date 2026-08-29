from __future__ import annotations
from pathlib import Path
from exporters import export_bond_key
from importers import load_bond_from_reg_file
from platform_detect import OSKind
from storage import ensure_exports_dir
import tui_helpers as tui
import actions_common as common
from actions_windows import run_offline_windows_export
from actions_verify import verify_and_connect, run_verify_flow  # noqa: F401
from actions_remove import run_remove_flow  # noqa: F401


def _ensure_device_name(bond) -> None:
    """If bond has no name, prompt the user to enter one interactively."""
    if not bond.device_name:
        name = tui.ask("Device has no name — enter a label (Enter to skip)", default="")
        if name.strip():
            bond.device_name = name.strip()


def run_export_flow() -> None:
    tui.header("Select & Extract — Step 1: System detection")
    env, backend = common.detect_and_validate()
    tui.header("Select & Extract — Step 2: Choose extraction source")
    source_os, win_mount = common.prompt_source_os(env.os_kind)
    if source_os == OSKind.WINDOWS and env.os_kind == OSKind.LINUX:
        run_offline_windows_export(win_mount, export_bond_key, ensure_exports_dir)
        return
    tui.header("Select & Extract — Step 3: Choose a device")
    with tui.Spinner("Scanning bonded BLE devices…"):
        devices = backend.list_devices()
    chosen = common.prompt_select_device(devices) if devices else None
    if not chosen:
        tui.info("No devices or cancelled.")
        return
    tui.header("Select & Extract — Step 4: Extract and save")
    with tui.Spinner(f"Extracting bonding for {chosen.device_mac}…"):
        bond = backend.extract_bond_key(chosen)
        bond.source_os = source_os.value
    common.print_bond_summary(bond)
    _ensure_device_name(bond)
    with tui.Spinner("Writing export files…"):
        exports_dir = ensure_exports_dir()
        reg_path = export_bond_key(bond)
    print()
    tui.ok(f"Exports folder : {tui.dim(str(exports_dir))}")
    tui.ok(f"File generated : {tui.bold(reg_path.name)}")
    tui.ok(f"Metadata (JSON): {tui.bold(reg_path.with_suffix('.json').name)}")


def _pick_adapter(backend, default_adapter: str | None = None) -> str | None:
    adapters = backend._list_adapters()
    if not adapters:
        tui.err("No Bluetooth adapters found in /var/lib/bluetooth.")
        return None
    if len(adapters) == 1:
        return adapters[0]
    print(f"\n  {tui.bold('Multiple Bluetooth adapters found on this system:')}\n")
    for i, a in enumerate(adapters, 1):
        mark = tui.green(" (matches file)") if a == default_adapter else ""
        print(f"    {tui.cyan(f'[{i}]')}  {a}{mark}")
    print()
    while True:
        raw = tui.ask("Adapter index")
        if raw.isdigit():
            idx = int(raw)
            if 1 <= idx <= len(adapters):
                return adapters[idx - 1]
        tui.warn("Invalid index, try again.")


def run_import_flow(reg_file_arg: str | None = None) -> None:
    tui.header("Import & Reconnect — Step 1: System detection")
    env, backend = common.detect_and_validate()
    if env.os_kind != OSKind.LINUX:
        tui.err("Import is only supported when running on Linux (target system).")
        return
    tui.header("Import & Reconnect — Step 2: Select file")
    reg_path = Path(reg_file_arg) if reg_file_arg else common.prompt_select_export_file()
    if not reg_path or not reg_path.exists():
        tui.err(f"File not found: {reg_path}")
        return
    tui.ok(f"File: {tui.bold(reg_path.name)}")
    tui.header("Import & Reconnect — Step 3: Inspect key")
    try:
        bond = load_bond_from_reg_file(reg_path)
    except Exception as e:
        tui.err(f"Failed to parse {reg_path.name}: {e}")
        return
    common.print_bond_summary(bond)
    tui.header("Import & Reconnect — Step 4: Map local device")
    chosen_adapter = _pick_adapter(backend, default_adapter=bond.adapter_mac)
    if not chosen_adapter:
        return
    bond.adapter_mac = chosen_adapter
    with tui.Spinner("Scanning existing devices in BlueZ…"):
        existing = backend.list_devices()
    local_match = next((d for d in existing if d.device_mac.upper() == bond.device_mac.upper()), None)
    ltk_match = None
    if not local_match:
        for d in existing:
            if d.has_ltk:
                try:
                    local_bond = backend.extract_bond_key(d)
                    if (local_bond.ltk_hex.upper() == bond.ltk_hex.upper() or
                        (bond.irk_hex and local_bond.irk_hex and
                         local_bond.irk_hex.upper() == bond.irk_hex.upper())):
                        ltk_match = d
                        if not bond.device_name and local_bond.device_name:
                            bond.device_name = local_bond.device_name
                        break
                except Exception:
                    pass
    source_device_mac = None
    if ltk_match:
        tui.info(f"Matched physical device under a different MAC address: {ltk_match.device_mac}")
        q = f"Migrate profile/cache from {ltk_match.device_mac} to {bond.device_mac}? [Y/n]"
        if tui.ask(q, default="Y").upper() == "Y":
            source_device_mac = ltk_match.device_mac
    elif local_match:
        tui.info("Device found locally but has no LTK.")
    else:
        tui.info("Device not paired locally yet.")

    print()
    target_mac = tui.ask("Destination MAC (Enter to keep original)", default=bond.device_mac)
    target_mac = target_mac if target_mac != bond.device_mac else None

    tui.header("Import — Step 5: Write and restart Bluetooth")
    with tui.Spinner("Writing bonding to disk…"):
        written_path = backend.import_bond_key(
            bond, target_device_mac=target_mac, source_device_mac=source_device_mac
        )
    tui.ok(f"Written to: {tui.dim(str(written_path))}")
    tui.info("Restarting Bluetooth service to apply changes. This may take a moment…")
    with tui.Spinner("Restarting Bluetooth service…"):
        backend.restart_bluetooth_stack()
    tui.ok("Bluetooth service restarted.")
    verify_and_connect(backend, target_mac or bond.device_mac)


def run_clone_flow() -> None:
    """Delegates to unified clone flow for BLE, Classic, and Dual-Mode."""
    from actions_clone import run_unified_clone_flow
    run_unified_clone_flow()
