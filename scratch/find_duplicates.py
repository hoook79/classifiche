import json
import os
import re
from collections import defaultdict, Counter

import sys
sys.path.append(os.getcwd())
from genera_html import normalize_name, build_global_canonical_mapping

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

# 1. Carica storia e calcola frequenze
global_song_counts = Counter()
for filename in HISTORY_FILES:
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            for item in data:
                global_song_counts[item['song']] += 1

years_cache = {}
overrides = {}
if os.path.exists('song_years_cache.json'):
    with open('song_years_cache.json', 'r', encoding='utf-8') as f:
        years_cache = json.load(f)
if os.path.exists('manual_years_override.json'):
    with open('manual_years_override.json', 'r', encoding='utf-8') as f:
        overrides = json.load(f)

# Genera mappatura globale
raw_to_canonical, canonical_to_spelling = build_global_canonical_mapping(global_song_counts, years_cache, overrides)

# Precompute mapping from cleaned song name to its canonical key
clean_to_canonical = {}
for raw_k in global_song_counts:
    cleaned_k = re.sub(r'\s*\(\d{4}\)\s*$', '', raw_k).strip()
    if raw_k in raw_to_canonical:
        clean_to_canonical[cleaned_k] = raw_to_canonical[raw_k]

# 2. Raggruppa tutte le canzoni uniche dello storico
all_songs = set()
for raw_name in global_song_counts:
    if not "PROMO" in raw_name.upper() and not "SPOT" in raw_name.upper():
        cleaned = re.sub(r'\s*\(\d{4}\)\s*$', '', raw_name).strip()
        all_songs.add(cleaned)

# Raggruppa per titolo normalizzato per la ricerca di doppioni
title_to_songs = defaultdict(list)
for song in all_songs:
    if ' - ' in song:
        artist, title = song.split(' - ', 1)
    else:
        artist, title = '', song
        
    norm_title = re.sub(r'[^a-z0-9]', '', title.lower())
    norm_title = re.sub(r'\b(feat|ft|featuring|with)\b.*$', '', norm_title, flags=re.I)
    norm_title = re.sub(r'[^a-z0-9]', '', norm_title)
    
    if norm_title:
        title_to_songs[norm_title].append(song)

print("Potenziali doppioni con lo stesso titolo ma chiavi canoniche diverse (dopo il raggruppamento globale):")
count = 0
for norm_title, songs in title_to_songs.items():
    if len(songs) > 1:
        for i in range(len(songs)):
            for j in range(i + 1, len(songs)):
                s1 = songs[i]
                s2 = songs[j]
                
                key1 = clean_to_canonical.get(s1)
                key2 = clean_to_canonical.get(s2)
                
                if key1 and key2 and key1 != key2:
                    a1 = s1.split(' - ')[0].lower() if ' - ' in s1 else s1.lower()
                    a2 = s2.split(' - ')[0].lower() if ' - ' in s2 else s2.lower()
                    
                    a1_clean = re.sub(r'[^a-z0-9 ]', '', a1)
                    a2_clean = re.sub(r'[^a-z0-9 ]', '', a2)
                    
                    words1 = set(a1_clean.split())
                    words2 = set(a2_clean.split())
                    
                    common_sig_words = {w for w in words1.intersection(words2) if len(w) > 3}
                    if common_sig_words:
                        print(f"\n  Titolo: '{norm_title}'")
                        print(f"    S1: '{s1}' (Canonica: {key1})")
                        print(f"    S2: '{s2}' (Canonica: {key2})")
                        print(f"    Parole in comune dell'artista: {common_sig_words}")
                        count += 1

print(f"\nTotale doppioni reali rimasti non uniti: {count}")
