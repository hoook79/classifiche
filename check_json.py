import json
from collections import defaultdict

with open('radio_divina_history.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

matches = defaultdict(list)
for item in data:
    key = (item['song'], item['time'])
    matches[key].append(item['date'])

count = 0
for key, dates in matches.items():
    if len(set(dates)) > 1:
        print(f"Song/Time: {key} found on dates: {set(dates)}")
        count += 1
        if count > 20: break

print(f"Total entries with same song/time on different dates: {count}")
