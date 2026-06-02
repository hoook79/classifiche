import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

cache_file = 'song_radiodates_cache.json'
if os.path.exists(cache_file):
    # Let's get modification time or check the values that have valid dates and are not Tiziano
    with open(cache_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    valid_dates = {k: v for k, v in data.items() if v != 'N/A' and v != 'N/D'}
    print("Total valid dates:", len(valid_dates))
    print("\nSample valid dates:")
    # Print the last 20 elements
    for k, v in list(valid_dates.items())[-20:]:
        print(f"  {k} -> {v}")
else:
    print("Cache file does not exist.")
