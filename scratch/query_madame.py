import json

with open('song_years_cache.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)

for k, v in cache.items():
    if 'MADAME' in k.upper():
        print(f"{k} -> {v}")
