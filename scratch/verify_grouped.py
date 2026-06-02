import json
import os
import re
from collections import defaultdict, Counter

import sys
sys.path.append(os.getcwd())
from genera_html import normalize_name

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

# Raccogli tutti i passaggi da tutti i file
all_plays = []
for filename in HISTORY_FILES:
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            for item in data:
                all_plays.append((filename, item['song']))

# Raggruppa i passaggi usando normalize_name
grouped_counts = defaultdict(int)
grouped_spellings = defaultdict(Counter)
grouped_radios = defaultdict(Counter)

for radio_file, song_name in all_plays:
    raw_name = re.sub(r'^SRS\s+', '', song_name).strip()
    if "PROMO" in raw_name.upper() or "SPOT" in raw_name.upper():
        continue
        
    norm_key = normalize_name(raw_name)
    
    # Estrai artista e titolo semplici per la visualizzazione
    cleaned = re.sub(r'\s*\(\d{4}\)\s*$', '', raw_name).strip()
    if ' - ' in cleaned:
        artist, title = cleaned.split(' - ', 1)
    else:
        artist, title = cleaned, ''
        
    grouped_counts[norm_key] += 1
    grouped_spellings[norm_key][(artist, title)] += 1
    grouped_radios[norm_key][radio_file] += 1

print("Verifica raggruppamento canzoni contenenti 'Bam Bam' in tutte le radio:")
for norm_key, count in sorted(grouped_counts.items(), key=lambda x: x[1], reverse=True):
    best_spelling = grouped_spellings[norm_key].most_common(1)[0][0]
    full_title = f"{best_spelling[0]} - {best_spelling[1]}"
    if "bam bam" in full_title.lower():
        print(f"\n  Chiave Normalizzata: {norm_key}")
        print(f"    Spelling scelto: {full_title}")
        print(f"    Conteggio totale passaggi (Tutte le radio): {count}")
        print(f"    Passaggi per radio:")
        for r_file, r_count in grouped_radios[norm_key].items():
            print(f"      - {r_file.replace('_history.json', '')}: {r_count} passaggi")
        print(f"    Grafie alternative trovate:")
        for spelling, spell_count in grouped_spellings[norm_key].items():
            print(f"      - {spelling[0]} - {spelling[1]} ({spell_count} volte)")
