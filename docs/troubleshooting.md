# Troubleshooting & Diagnostics

This guide covers common issues, error messages, and diagnosis steps when synchronizing Bluetooth keys.

---

## 1. Diagnostic Checklist

Run diagnostic inspection on the device:
```bash
# Check device pairing and trust state in BlueZ
bluetoothctl info <DEVICE_MAC>

# Monitor Bluetooth HCI packets live during connection attempts
sudo btmon
```

---

## 2. Common Errors and Resolutions

### `br-connection-page-timeout` (Classic Devices)
- **Symptom**: `bluetoothctl connect <MAC>` fails with `Failed to connect: org.bluez.Error.Failed br-connection-page-timeout`.
- **Cause**: Radio paging failure. The physical device is either:
  1. Powered off or out of range.
  2. Actively connected to or remembering a different host.
  3. Discarded its single internal bonding slot due to repeated power cycling or pressing pairing button.
- **Fix**: Turn device off, wait 3 seconds, turn it on, and run `bluetoothctl connect <MAC>` without pressing pairing buttons.

### `org.bluez.Error.AuthenticationFailed` / `AuthenticationCanceled`
- **Symptom**: Link key or LTK rejected by peripheral.
- **Cause**: The key on disk does not match the key inside peripheral NVRAM.
- **Fix**: Re-pair the device cleanly on source OS, immediately extract keys without power cycling, and re-import to destination OS.

### Daemon In-Memory Cache Not Updating
- **Symptom**: Modifying `/var/lib/bluetooth/.../info` does not take effect.
- **Cause**: BlueZ caches bonding files in memory upon startup and does not watch disk events.
- **Fix**: Always restart the daemon via `sudo systemctl restart bluetooth` (handled automatically by `btkey_sync`).

### Missing Windows Registry Keys
- **Symptom**: Windows elevation fails or `BTHPORT\Parameters\Keys` is empty.
- **Cause**: Standard Administrator account lacks read permissions on `HKLM\SYSTEM\CurrentControlSet\Services\BTHPORT\Parameters\Keys`.
- **Fix**: Use temporary SYSTEM scheduled task (`schtasks /create /ru "NT AUTHORITY\SYSTEM"`) as automated in `WindowsBluetoothBackend`.
