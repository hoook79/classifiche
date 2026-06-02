import json
import subprocess
import sys

# Imposta codifica UTF-8
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

cache_file = 'song_radiodates_cache.json'
with open(cache_file, 'r', encoding='utf-8') as f:
    cache = json.load(f)

# Aggiorna il valore per Amore di Contrabbando
key = "CRISTIANO MALGIOGLIO - Amore di Contrabbando"
print(f"Old value: {cache.get(key)}")
cache[key] = "22/05/2026"
print(f"New value: {cache.get(key)}")

with open(cache_file, 'w', encoding='utf-8') as f:
    json.dump(cache, f, indent=2, ensure_ascii=False)

print("Cache updated successfully!")

# Rigenera HTML
print("Regenerating classifica_radio.html...")
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
