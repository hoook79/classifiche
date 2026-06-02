import json

with open('song_radiodates_cache.json', 'r', encoding='utf-8') as f:
    dates_cache = json.load(f)

with open('song_years_cache.json', 'r', encoding='utf-8') as f:
    years_cache = json.load(f)

count_recent_na = 0
for k, v in dates_cache.items():
    if v == 'N/A':
        y = years_cache.get(k, 'N/A')
        try:
            if y != 'N/A' and int(y) >= 2025:
                count_recent_na += 1
                print(f"Recent N/A: {k} (Year: {y})")
        except ValueError:
            pass

print(f"Total recent N/A songs: {count_recent_na}")
