"""
tests/test_parsing.py

Consolidated test suite and regression runner.
Respects 200-line limit (AGENTS.md R14).
"""

from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backends.offline_windows import _read_reg_file
from tests.test_parsing_ble import (  # noqa: F401
    BLE_TESTS,
    test_parse_real_mouse_reg,
    test_bondkey_normalizes_mac_without_separators,
    test_bondkey_rejects_invalid_ltk_length,
    test_roundtrip_reg_export_matches_original_values,
    test_roundtrip_with_different_target_mac,
    test_parse_irk_and_addresstype,
)
from tests.test_parsing_classic import (  # noqa: F401
    CLASSIC_TESTS,
    test_link_key_bond_validates_key_length,
    test_link_key_bond_normalizes_macs,
    test_link_key_bond_rejects_invalid_hex,
    test_parse_classic_from_reg_text_placeholder,
    test_write_classic_info_produces_complete_file,
    test_classic_exporter_importer_roundtrip,
)


def test_read_reg_file_utf8_and_utf16():
    """Verify _read_reg_file parses both reged UTF-8 output and Windows UTF-16LE."""
    sample_text = 'Windows Registry Editor Version 5.00\r\n\r\n[HKEY_LOCAL_MACHINE\\SYSTEM\\Select]\r\n"Current"=dword:00000002\r\n'

    with tempfile.NamedTemporaryFile(suffix=".reg", mode="wb", delete=False) as tf:
        tf.write(sample_text.encode("utf-8"))
        p_utf8 = Path(tf.name)

    with tempfile.NamedTemporaryFile(suffix=".reg", mode="wb", delete=False) as tf:
        tf.write(b"\xff\xfe" + sample_text.encode("utf-16-le"))
        p_utf16 = Path(tf.name)

    try:
        assert '"Current"=dword:00000002' in _read_reg_file(p_utf8)
        assert '"Current"=dword:00000002' in _read_reg_file(p_utf16)
    finally:
        p_utf8.unlink(missing_ok=True)
        p_utf16.unlink(missing_ok=True)


NEW_TESTS = [
    test_read_reg_file_utf8_and_utf16,
]


def run_all_tests() -> int:
    all_tests = BLE_TESTS + CLASSIC_TESTS + NEW_TESTS
    failures = 0
    for t in all_tests:
        try:
            t()
            print(f"OK   {t.__name__}")
        except Exception as e:
            failures += 1
            print(f"FAIL {t.__name__}: {e}")
    print(f"\n{len(all_tests) - failures}/{len(all_tests)} tests pasaron")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(run_all_tests())
