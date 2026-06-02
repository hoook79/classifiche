import subprocess
import json

try:
    res = subprocess.run(["powershell", "-Command", "Get-Process python | ForEach-Object { $_.Id }"], capture_output=True, text=True)
    pids = [p.strip() for p in res.stdout.splitlines() if p.strip()]
    for pid in pids:
        res2 = subprocess.run(["powershell", "-Command", f"(Get-CimInstance Win32_Process -Filter 'ProcessId = {pid}').CommandLine"], capture_output=True, text=True)
        print(f"PID {pid}: {res2.stdout.strip()}")
except Exception as e:
    print(f"Error: {e}")
