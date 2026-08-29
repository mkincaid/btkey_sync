"""
tests/test_parsing_ble.py

BLE parsing and conversion tests using real hardware bond data.
Respects 200-line limit (AGENTS.md R14).
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backends.windows_backend import parse_windows_reg_text
from exporters.reg_exporter import build_windows_reg_content
from models import BondKey

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_mouse.reg"

EXPECTED_ADAPTER_MAC = "70:08:94:93:77:78"
EXPECTED_DEVICE_MAC = "68:78:56:11:35:AD"
EXPECTED_LTK = "33221166554499887722110055443366"
EXPECTED_EDIV = 16135
EXPECTED_ERAND = 15463799465814456318
EXPECTED_AUTHREQ = 0x2D


def test_parse_real_mouse_reg():
    text = FIXTURE_PATH.read_text(encoding="utf-8-sig")
    bond = parse_windows_reg_text(text)
    assert bond.adapter_mac == EXPECTED_ADAPTER_MAC
    assert bond.device_mac == EXPECTED_DEVICE_MAC
    assert bond.ltk_hex == EXPECTED_LTK
    assert bond.ediv == EXPECTED_EDIV
    assert bond.erand == EXPECTED_ERAND
    assert bond.auth_req == EXPECTED_AUTHREQ


def test_bondkey_normalizes_mac_without_separators():
    bond = BondKey(
        adapter_mac="700894937778",
        device_mac="6878561135ad",
        ltk_hex=EXPECTED_LTK,
        ediv=EXPECTED_EDIV,
        erand=EXPECTED_ERAND,
    )
    assert bond.adapter_mac == EXPECTED_ADAPTER_MAC
    assert bond.device_mac == EXPECTED_DEVICE_MAC


def test_bondkey_rejects_invalid_ltk_length():
    try:
        BondKey(
            adapter_mac=EXPECTED_ADAPTER_MAC,
            device_mac=EXPECTED_DEVICE_MAC,
            ltk_hex="deadbeef",
            ediv=1,
            erand=1,
        )
        assert False, "Debió lanzar ValueError por LTK inválido"
    except ValueError:
        pass


def test_roundtrip_reg_export_matches_original_values():
    original_text = FIXTURE_PATH.read_text(encoding="utf-8-sig")
    bond = parse_windows_reg_text(original_text)

    regenerated_text = build_windows_reg_content(bond)
    bond_again = parse_windows_reg_text(regenerated_text)

    assert bond_again.adapter_mac == bond.adapter_mac
    assert bond_again.device_mac == bond.device_mac
    assert bond_again.ltk_hex == bond.ltk_hex
    assert bond_again.ediv == bond.ediv
    assert bond_again.erand == bond.erand
    assert bond_again.auth_req == bond.auth_req


def test_roundtrip_with_different_target_mac():
    original_text = FIXTURE_PATH.read_text(encoding="utf-8-sig")
    bond = parse_windows_reg_text(original_text)

    new_mac = "AA:BB:CC:DD:EE:FF"
    regenerated_text = build_windows_reg_content(bond, target_device_mac=new_mac)
    bond_again = parse_windows_reg_text(regenerated_text)

    assert bond_again.device_mac == new_mac
    assert bond_again.ltk_hex == bond.ltk_hex
    assert bond_again.ediv == bond.ediv
    assert bond_again.erand == bond.erand


def test_parse_irk_and_addresstype():
    text = (
        "Windows Registry Editor Version 5.00\r\n\r\n"
        "[HKEY_LOCAL_MACHINE\\SYSTEM\\ControlSet001\\Services\\BTHPORT\\Parameters\\Keys\\700894937778\\d4c1b57106bb]\r\n"
        '"LTK"=hex:ee,07,60,40,eb,c4,1e,8a,17,e9,4b,12,53,6e,37,a2\r\n'
        '"KeyLength"=dword:00000010\r\n'
        '"ERand"=hex(b):00,00,00,00,00,00,00,00\r\n'
        '"EDIV"=dword:00000000\r\n'
        '"IRK"=hex:fe,aa,17,a8,27,96,a4,c0,ed,f2,d6,76,ce,40,34,fd\r\n'
        '"AddressType"=dword:00000001\r\n'
    )
    bond = parse_windows_reg_text(text)
    assert bond.irk_hex == "FEAA17A82796A4C0EDF2D676CE4034FD"
    assert bond.address_type == 1

    regenerated = build_windows_reg_content(bond)
    bond_again = parse_windows_reg_text(regenerated)
    assert bond_again.irk_hex == "FEAA17A82796A4C0EDF2D676CE4034FD"
    assert bond_again.address_type == 1


BLE_TESTS = [
    test_parse_real_mouse_reg,
    test_bondkey_normalizes_mac_without_separators,
    test_bondkey_rejects_invalid_ltk_length,
    test_roundtrip_reg_export_matches_original_values,
    test_roundtrip_with_different_target_mac,
    test_parse_irk_and_addresstype,
]
