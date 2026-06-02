import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Search for Superstar or Tiziano Ferro in the various history files
radios = ['subasio', 'divina', 'mitology', 'nostalgia', 'toscana', 'italia', 'rds', 'rtl1025']
for r in radios:
    p = f"radio_{r}_history.json"
    if os.path.exists(p):
        with open(p, 'r', encoding='utf-8') as f:
            data = json.load(f)
        matches = set()
        for item in data:
            s = item.get('song', '')
            if 'superstar' in s.lower() or 'tiziano' in s.lower():
                matches.add(s)
        if matches:
            print(f"--- {r} ---")
            for m in sorted(matches):
                print(f"  {m}")

print("\n--- Cache Years ---")
if os.path.exists('song_years_cache.json'):
    with open('song_years_cache.json', 'r', encoding='utf-8') as f:
        cache = json.load(f)
    for k, v in cache.items():
        if 'superstar' in k.lower() or 'tiziano' in k.lower():
            print(f"  {k}: {v}")

print("\n--- Cache Overrides ---")
if os.path.exists('manual_years_override.json'):
    with open('manual_years_override.json', 'r', encoding='utf-8') as f:
        cache = json.load(f)
    for k, v in cache.items():
        if 'superstar' in k.lower() or 'tiziano' in k.lower():
            print(f"  {k}: {v}")
