"""
tests/test_power_on.py

Regression tests for powering the adapter back on after a BlueZ restart.
bluetoothctl/rfkill/systemctl are faked; no Bluetooth hardware is needed.
"""

from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backends import linux_common as lc


class FakeBluez:
    """Adapter that is not registered for `delay` polls, then needs rfkill cleared."""

    def __init__(self, registered_after=0, soft_blocked=False):
        self.polls = 0
        self.registered_after = registered_after
        self.soft_blocked = soft_blocked
        self.powered = False
        self.calls = []

    def run(self, cmd, **kwargs):
        self.calls.append(cmd)
        out = ""
        if cmd[0] == "rfkill":
            self.soft_blocked = False
        elif cmd[:2] == ["bluetoothctl", "power"]:
            self.polls += 1
            if self.polls <= self.registered_after:
                out = "No default controller available\n"
            elif self.soft_blocked:
                out = "Failed to set power on: org.bluez.Error.Blocked\n"
            else:
                self.powered = True
                out = "Changing power on succeeded\n"
        elif cmd[:2] == ["bluetoothctl", "show"]:
            out = f"Controller AA:BB:CC:DD:EE:FF\n\tPowered: {'yes' if self.powered else 'no'}\n"
        return subprocess.CompletedProcess(cmd, 0, stdout=out, stderr="")


def _patch(monkeypatch, fake):
    monkeypatch.setattr(lc.subprocess, "run", fake.run)
    monkeypatch.setattr(lc.shutil, "which", lambda name: "/usr/sbin/" + name)
    monkeypatch.setattr(lc.time, "sleep", lambda s: None)


def test_power_on_waits_for_adapter_registration(monkeypatch):
    fake = FakeBluez(registered_after=3)
    _patch(monkeypatch, fake)
    ok, _ = lc.power_on_adapter(timeout_s=30)
    assert ok and fake.powered


def test_power_on_clears_rfkill_soft_block(monkeypatch):
    fake = FakeBluez(soft_blocked=True)
    _patch(monkeypatch, fake)
    ok, _ = lc.power_on_adapter(timeout_s=30)
    assert ok and fake.powered


def test_power_on_reports_failure_instead_of_hiding_it(monkeypatch):
    fake = FakeBluez(registered_after=10**6)
    _patch(monkeypatch, fake)
    clock = iter(range(0, 1000, 5))
    monkeypatch.setattr(lc.time, "monotonic", lambda: next(clock))
    ok, detail = lc.power_on_adapter(timeout_s=20)
    assert not ok and "No default controller" in detail


def test_restart_returns_power_status(monkeypatch):
    fake = FakeBluez()
    _patch(monkeypatch, fake)
    ok, _ = lc.restart_bluetooth_daemon()
    assert ok
    assert ["systemctl", "restart", "bluetooth"] in fake.calls


POWER_TESTS = [
    test_power_on_waits_for_adapter_registration,
    test_power_on_clears_rfkill_soft_block,
    test_power_on_reports_failure_instead_of_hiding_it,
    test_restart_returns_power_status,
]
