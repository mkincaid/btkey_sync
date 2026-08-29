"""
tests/test_parsing_classic.py

Classic (BR/EDR) parsing and integration tests.
Respects 200-line limit (AGENTS.md R14).
"""

import configparser
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backends.linux_classic import write_classic_info
from backends.windows_common import parse_classic_from_reg_text
from exporters.classic_exporter import build_classic_reg_content
from importers.classic_importer import load_classic_bond_from_reg_file
from models import LinkKeyBond

_GOOD_KEY = "0102030405060708090A0B0C0D0E0F10"
_ADAPTER = "AA:BB:CC:DD:EE:FF"
_DEVICE = "11:22:33:44:55:66"

_CLASSIC_REG_TEXT = (
    "Windows Registry Editor Version 5.00\r\n\r\n"
    "[HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\BTHPORT"
    "\\Parameters\\Keys\\aabbccddeeff]\r\n"
    '"112233445566"=hex:01,02,03,04,05,06,07,08,09,0a,0b,0c,0d,0e,0f,10\r\n'
)


def test_link_key_bond_validates_key_length():
    for bad_key in ("AABBCC" * 5, "00" * 17):
        try:
            LinkKeyBond(
                adapter_mac=_ADAPTER, device_mac=_DEVICE,
                link_key_hex=bad_key, key_type=4, pin_length=0, device_class="",
            )
            assert False, f"Should have raised ValueError for key: {bad_key!r}"
        except ValueError:
            pass


def test_link_key_bond_normalizes_macs():
    bond = LinkKeyBond(
        adapter_mac="aabbccddeeff",
        device_mac="112233445566",
        link_key_hex=_GOOD_KEY,
        key_type=4, pin_length=0, device_class="",
    )
    assert bond.adapter_mac == _ADAPTER
    assert bond.device_mac == _DEVICE
    assert bond.mac_nodelim == "112233445566"
    assert bond.adapter_mac_nodelim == "aabbccddeeff"


def test_link_key_bond_rejects_invalid_hex():
    bad_key = "ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ"
    try:
        LinkKeyBond(
            adapter_mac=_ADAPTER, device_mac=_DEVICE,
            link_key_hex=bad_key, key_type=4, pin_length=0, device_class="",
        )
        assert False, "Should have raised ValueError for non-hex key"
    except ValueError:
        pass


def test_parse_classic_from_reg_text_placeholder():
    bonds = parse_classic_from_reg_text(_CLASSIC_REG_TEXT)
    assert len(bonds) == 1, f"Expected 1 bond, got {len(bonds)}"
    b = bonds[0]
    assert b.adapter_mac == "AA:BB:CC:DD:EE:FF"
    assert b.device_mac == "11:22:33:44:55:66"
    assert b.link_key_hex == "0102030405060708090A0B0C0D0E0F10"
    assert b.source_os == "windows"
    assert b.mac_nodelim == "112233445566"


def test_write_classic_info_produces_complete_file():
    bond = LinkKeyBond(
        adapter_mac="AA:BB:CC:DD:EE:FF",
        device_mac="11:22:33:44:55:66",
        link_key_hex=_GOOD_KEY,
        key_type=4,
        pin_length=0,
        device_class="0x002540",
        device_name="Test Keyboard",
        device_id={"source": "1", "vendor": "0x045E", "product": "0x0800", "version": "0x0001"},
        service_uuids=["00001124-0000-1000-8000-00805f9b34fb"],
        source_os="linux",
    )

    with tempfile.TemporaryDirectory() as tmp:
        target_dir = Path(tmp) / "AA:BB:CC:DD:EE:FF" / "11:22:33:44:55:66"
        info_path = write_classic_info(bond, target_dir)

        assert info_path.exists(), "info file was not created"

        cfg = configparser.ConfigParser()
        cfg.optionxform = str
        cfg.read(info_path)

        assert "General" in cfg
        assert cfg["General"]["SupportedTechnologies"] == "BR/EDR;"
        assert cfg["General"]["Class"] == bond.device_class
        assert cfg["General"]["Trusted"] == "true"

        assert "LinkKey" in cfg
        assert cfg["LinkKey"]["Key"] == bond.link_key_hex
        assert cfg["LinkKey"]["Type"] == str(bond.key_type)
        assert cfg["LinkKey"]["PINLength"] == str(bond.pin_length)

        assert "DeviceID" in cfg
        assert cfg["DeviceID"]["Source"] == "1"


def test_classic_exporter_importer_roundtrip():
    original = LinkKeyBond(
        adapter_mac=_ADAPTER,
        device_mac=_DEVICE,
        link_key_hex=_GOOD_KEY,
        key_type=4,
        pin_length=0,
        device_class="0x002540",
        device_name="Round-trip Keyboard",
        source_os="linux",
    )

    reg_text = build_classic_reg_content(original)
    assert '[HKEY_LOCAL_MACHINE' in reg_text
    assert f'\\{original.adapter_mac_nodelim}]' in reg_text
    assert f'"{original.mac_nodelim}"=hex:' in reg_text

    with tempfile.NamedTemporaryFile(suffix=".reg", mode="w", delete=False, encoding="utf-8") as tf:
        tf.write(reg_text)
        tmp_path = Path(tf.name)

    try:
        reloaded = load_classic_bond_from_reg_file(tmp_path)
        assert reloaded.adapter_mac == original.adapter_mac
        assert reloaded.device_mac == original.device_mac
        assert reloaded.link_key_hex == original.link_key_hex
    finally:
        tmp_path.unlink(missing_ok=True)


CLASSIC_TESTS = [
    test_link_key_bond_validates_key_length,
    test_link_key_bond_normalizes_macs,
    test_link_key_bond_rejects_invalid_hex,
    test_parse_classic_from_reg_text_placeholder,
    test_write_classic_info_produces_complete_file,
    test_classic_exporter_importer_roundtrip,
]
