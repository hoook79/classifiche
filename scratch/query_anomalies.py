import json

with open('song_years_cache.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)

targets = [
    "MADAME - Voce",
    "MADAME, MARRACASH - Volevo Capire Con Marracash",
    "NOEMI - TU COSA FAI QUESTA SERA CON VITO SALAMANCA",
    "FEDERICA ABBATE - SUPERMAN",
    "BENIAMINO GIGLI - MAMMA"
]

for t in targets:
    print(f"{t} -> {cache.get(t, 'Not in Cache')}")
