import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

years_file = "song_years_cache.json"
dates_file = "song_radiodates_cache.json"

if os.path.exists(years_file) and os.path.exists(dates_file):
    with open(years_file, "r", encoding="utf-8") as f:
        years_cache = json.load(f)
    with open(dates_file, "r", encoding="utf-8") as f:
        dates_cache = json.load(f)

    # Trova canzoni del 2025/2026 che hanno radio date "N/A"
    to_clear = set()
    for song, yr in years_cache.items():
        if yr in ["2025", "2026"]:
            # Cerca nella cache delle radio date con case-insensitive
            for dk in list(dates_cache.keys()):
                if dk.lower() == song.lower() and dates_cache[dk] == "N/A":
                    to_clear.add(dk)

    # Aggiungiamo esplicitamente Masini per sicurezza
    for dk in list(dates_cache.keys()):
        if "e poi ti ho visto cadere" in dk.lower() and dates_cache[dk] == "N/A":
            to_clear.add(dk)

    print(f"Trovate {len(to_clear)} canzoni uniche del 2025/2026 con radio date 'N/A':")
    for dk in sorted(to_clear):
        print(f"  - {dk} (Anno: {years_cache.get(dk, 'Unknown')})")

    if to_clear:
        # Rimuovile dalla cache delle radio date per permettere lo scraping
        removed_count = 0
        for dk in to_clear:
            if dk in dates_cache:
                del dates_cache[dk]
                removed_count += 1
        
        with open(dates_file, "w", encoding="utf-8") as f:
            json.dump(dates_cache, f, indent=2, ensure_ascii=False)
        print(f"\nRimosse con successo {removed_count} canzoni dalla cache delle radio date. Verranno raschiate al prossimo avvio!")
    else:
        print("\nNessuna canzone da rimuovere.")
else:
    print("File di cache non trovati.")
