import json

with open('song_radiodates_cache.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)

for k, v in cache.items():
    if 'CONTRABBANDO' in k.upper():
        print(f"{k} -> {v}")
