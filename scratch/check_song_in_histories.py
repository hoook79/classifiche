import os
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

HISTORY_FILES = [
    'radio_subasio_history.json',
    'radio_divina_history.json',
    'radio_mitology_history.json',
    'radio_nostalgia_history.json',
    'radio_toscana_history.json',
    'radio_italia_history.json',
    'radio_rds_history.json',
    'radio_rtl1025_history.json'
]

found = False
for file in HISTORY_FILES:
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for item in data:
            song = item.get('song', '')
            if "poi ti ho visto cadere" in song.lower():
                print(f"Trovata in {file}: '{song}'")
                found = True

if not found:
    print("Nessuna occorrenza trovata nelle cronologie storiche!")
