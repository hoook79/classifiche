import json

with open('song_years_cache.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)

na_count = sum(1 for v in cache.values() if v == 'N/A')
valid_count = sum(1 for v in cache.values() if v != 'N/A')
print(f"Total: {len(cache)}")
print(f"Valid: {valid_count}")
print(f"N/A: {na_count}")
