import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

cache_file = 'song_radiodates_cache.json'
if os.path.exists(cache_file):
    print("Cache file exists. Size:", os.path.getsize(cache_file))
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print("Total songs in cache:", len(data))
        # Print a few examples that are not 'N/D'
        non_nd = {k: v for k, v in data.items() if v != 'N/D'}
        print("Resolved songs (not N/D):", len(non_nd))
        for k, v in list(non_nd.items())[:15]:
            print(f"  {k} -> {v}")
    except Exception as e:
        print("Error reading cache:", e)
else:
    print("Cache file does not exist yet at:", cache_file)
