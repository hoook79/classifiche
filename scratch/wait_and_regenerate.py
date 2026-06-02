import subprocess
import time
import sys
import os

# Imposta codifica UTF-8
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

target_pid = 11204
print(f"Waiting for PID {target_pid} (heal_years_cache.py) to exit...")

def is_running(pid):
    try:
        # ps -p pid on windows: Get-Process -Id pid
        res = subprocess.run(["powershell", "-Command", f"Get-Process -Id {pid}"], capture_output=True, text=True)
        return res.returncode == 0
    except Exception:
        return False

# Attendi finché il processo non è più attivo
while is_running(target_pid):
    time.sleep(2)

print(f"PID {target_pid} has exited! Regenerating classifica_radio.html...")

creation_flags = 0
if sys.platform == 'win32':
    creation_flags = 0x08000000  # CREATE_NO_WINDOW

res = subprocess.run([sys.executable, 'genera_html.py'], capture_output=True, text=True, creationflags=creation_flags)
print("Stdout from genera_html.py:")
print(res.stdout)
if res.stderr:
    print("Stderr from genera_html.py:")
    print(res.stderr)

print("Regeneration complete!")
