import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

cache_file = 'song_radiodates_cache.json'
if os.path.exists(cache_file):
    with open(cache_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    valid_dates = {}
    na_count = 0
    nd_count = 0
    other_count = 0
    
    for k, v in data.items():
        if v == 'N/A':
            na_count += 1
        elif v == 'N/D':
            nd_count += 1
        else:
            valid_dates[k] = v
            
    print(f"Total entries: {len(data)}")
    print(f"N/A entries: {na_count}")
    print(f"N/D entries: {nd_count}")
    print(f"Valid dates: {len(valid_dates)}")
    print("\nSample valid dates:")
    for k, v in list(valid_dates.items())[:15]:
        print(f"  {k} -> {v}")
else:
    print("Cache file does not exist.")
