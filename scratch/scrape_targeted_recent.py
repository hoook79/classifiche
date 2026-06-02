import json
import os
import sys
import time

sys.path.append(r'c:\Users\Jonny\Desktop\REPORT CANZONI RADIO')
from scrape_earone_radiodates import (
    load_json, save_json, search_earone, search_earone_via_web, 
    split_artist_title, match_score, format_date, CACHE_FILE, YEARS_CACHE_FILE
)

sys.stdout.reconfigure(encoding='utf-8')

# 1. Carica le cache
dates_cache = load_json(CACHE_FILE)
years_cache = load_json(YEARS_CACHE_FILE)

# 2. Identifica le canzoni recenti (2025/2026) che mancano nella cache delle radio date
target_songs = []
for song, yr in years_cache.items():
    if yr in ["2025", "2026"]:
        if song not in dates_cache or dates_cache[song] in ["N/A", "N/D"]:
            target_songs.append(song)

# Aggiungiamo esplicitamente Masini per sicurezza
special_masini = "MARCO MASINI - E poi ti ho visto cadere"
if special_masini not in dates_cache or dates_cache[special_masini] in ["N/A", "N/D"]:
    if special_masini not in target_songs:
        target_songs.append(special_masini)

# PRIORITIZZA MARCO MASINI PER PRIMO!
target_songs.sort(key=lambda s: 0 if "masini" in s.lower() else 1)

print(f"=== AVVIO SCRAPING TARGETED PER {len(target_songs)} CANZONI RECENTI (ORDINATE) ===")
for s in target_songs:
    if "masini" in s.lower():
        print(f"  - [PRIORITARIO] {s}")
    else:
        print(f"  - {s}")

print("\nAvvio elaborazione...")
resolved_count = 0

for song in target_songs:
    print(f"\nElaborazione: '{song}'")
    db_art, db_tit = split_artist_title(song)
    
    # Step 1: Cerca su EarOne con Artist + Title
    print(f"  [STEP 1] Cerca internal: '{db_art} {db_tit}'")
    results = search_earone(f"{db_art} {db_tit}")
    
    best_score = 0
    best_item = None
    for res in results:
        res_song = res.get('song', {})
        res_artists = ", ".join([a.get('name') for a in res_song.get('tracks', [{}])[0].get('artists', [])]) if res_song.get('tracks') else "Unknown"
        res_title = res_song.get('title', '')
        score = match_score(db_art, db_tit, res_artists, res_title)
        if score > best_score:
            best_score = score
            best_item = res
            
    if best_item and best_score >= 80:
        formatted = format_date(best_item.get('radioDate'))
        dates_cache[song] = formatted
        resolved_count += 1
        print(f"  -> [SUCCESS 1] Trovato match: {formatted} (Score: {best_score})")
        save_json(dates_cache, CACHE_FILE)
        time.sleep(1.5)
        continue

    # Step 2: Cerca su EarOne con solo Title (Title-only)
    print(f"  [STEP 2] Cerca internal (Solo Titolo): '{db_tit}'")
    results_title = search_earone(db_tit)
    
    best_score = 0
    best_item = None
    for res in results_title:
        res_song = res.get('song', {})
        res_artists = ", ".join([a.get('name') for a in res_song.get('tracks', [{}])[0].get('artists', [])]) if res_song.get('tracks') else "Unknown"
        res_title = res_song.get('title', '')
        score = match_score(db_art, db_tit, res_artists, res_title)
        if score > best_score:
            best_score = score
            best_item = res
            
    if best_item and best_score >= 80:
        formatted = format_date(best_item.get('radioDate'))
        dates_cache[song] = formatted
        resolved_count += 1
        print(f"  -> [SUCCESS 2] Trovato match: {formatted} (Score: {best_score})")
        save_json(dates_cache, CACHE_FILE)
        time.sleep(1.5)
        continue

    # Step 3: Cerca via Web Fallback (Yahoo + Bing)
    print(f"  [STEP 3] Fallback Web Search...")
    web_date = search_earone_via_web(song)
    if web_date != "N/A":
        dates_cache[song] = web_date
        resolved_count += 1
        print(f"  -> [SUCCESS 3] Trovato via Web: {web_date}")
    else:
        dates_cache[song] = "N/A"
        print(f"  -> [FAILED] Non trovato su EarOne o Web. Salvato come N/A")
        
    save_json(dates_cache, CACHE_FILE)
    time.sleep(1.5)

print(f"\nFatto! Risolti {resolved_count}/{len(target_songs)} brani.")

# 3. Rigenera l'HTML
print("\n=== RIGENERAZIONE HTML IN CORSO ===")
import subprocess
sub_res = subprocess.run(["python", "genera_html.py"], capture_output=True, text=True, encoding='utf-8', errors='ignore')
print(sub_res.stdout)
