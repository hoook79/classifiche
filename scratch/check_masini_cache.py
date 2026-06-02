import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

cache_file = "song_radiodates_cache.json"
if os.path.exists(cache_file):
    with open(cache_file, "r", encoding="utf-8") as f:
        cache = json.load(f)
    
    # Cerca chiavi simili a Masini
    matches = {k: v for k, v in cache.items() if "masini" in k.lower()}
    print(f"Found {len(matches)} matches for 'masini':")
    for k, v in matches.items():
        print(f"  {k} -> {v}")
else:
    print(f"Cache file {cache_file} does not exist!")
