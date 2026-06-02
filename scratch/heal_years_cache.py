import json
import os
import re
import subprocess
import sys

# Imposta codifica UTF-8
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

CACHE_FILE = 'song_years_cache.json'
OVERRIDE_FILE = 'manual_years_override.json'

ARTIST_DEBUT_MAP = {
    'GAZZELLE': 2016,
    'BLANCO': 2020,
    'PINGUINI TATTICI NUCLEARI': 2012,
    'PTN': 2012,
    'TANANAI': 2019,
    'MAHMOOD': 2015,
    'IRAMA': 2015,
    'OLLY': 2019,
    'ACHILLE LAURO': 2012,
    'ANNALISA': 2011,
    'MARCO MENGONI': 2009,
    'TIZIANO FERRO': 2001,
    'LAURA PAUSINI': 1993,
    'EROS RAMAZZOTTI': 1982,
    'NEGRAMARO': 2001,
    'ALF': 2018,  # ALFA
    'ALFA': 2018,
    'COMA COSE': 2017,
    'ANGELINA MANGO': 2020,
    'ULTIMO': 2017,
    'ELODIE': 2015,
    'THE WEEKND': 2010,
    'COLDPLAY': 1998,
    'BEYONCÉ': 1997,
    'ED SHEERAN': 2005,
    'OASIS': 1991,
    '883': 1989,
    'MAX PEZZALI': 1989,
    'VASCO ROSSI': 1977,
    'ZUCCHERO': 1970,
    'LIGABUE': 1987,
    'TOMMASO PARADISO': 2011,
    'THE KOLORS': 2010,
    'SFERA EBBASTA': 2013,
    'LAZZA': 2012,
    'GHALI': 2011,
    'MR RAIN': 2011,
    'MR.RAIN': 2011,
    'ARIETE': 2019,
    'BOOMDABASH': 2002,
    'FEDERICA ABBATE': 2013,
    'ROSE VILLAIN': 2016,
    'GEOLIER': 2018,
    'TEDUA': 2014,
    'CAPO PLAZA': 2016,
    'RONDODASOSA': 2020,
    'MADAME': 2018,
    'ALESSANDRA AMOROSO': 2008,
    'EMMA': 2010,
    'NOEMI': 2009,
    'FULMINACCI': 2019,
    'FRANCESCO GABBANI': 2010,
}

def load_json(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except Exception as e:
                print(f"Error loading {filepath}: {e}")
                return {}
    return {}

def save_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def split_song(key):
    if " - " in key:
        parts = key.split(" - ", 1)
        return parts[0].strip(), parts[1].strip()
    return "Unknown", key.strip()

def main():
    print("=== HEAL YEARS CACHE ===")
    cache = load_json(CACHE_FILE)
    overrides = load_json(OVERRIDE_FILE)
    
    anomalies_cleared = []
    
    for song_key, year in list(cache.items()):
        if song_key in overrides:
            continue
        if not year or year == "N/A":
            continue
        if not year.isdigit():
            print(f"Clearing non-numeric year for {song_key}: {year}")
            cache[song_key] = "N/A"
            anomalies_cleared.append(song_key)
            continue
            
        y_int = int(year)
        
        # Anno nel futuro
        if y_int > 2026:
            print(f"Clearing future year for {song_key}: {year}")
            cache[song_key] = "N/A"
            anomalies_cleared.append(song_key)
            continue
            
        # Anno prima del debutto dell'artista
        artist, title = split_song(song_key)
        artist_upper = artist.upper()
        
        has_veto = False
        for a_key, debut_y in ARTIST_DEBUT_MAP.items():
            if a_key == 'ANNALISA' and 'ANNALISA MINETTI' in artist_upper:
                continue
            if a_key == 'OLLY' and 'OLLY MURS' in artist_upper:
                continue
                
            pattern = r'\b' + re.escape(a_key) + r'\b'
            if re.search(pattern, artist_upper):
                if y_int < debut_y:
                    print(f"Clearing historical anomaly for {song_key}: {year} < debut of {a_key} ({debut_y})")
                    cache[song_key] = "N/A"
                    anomalies_cleared.append(song_key)
                    has_veto = True
                    break
                    
    if anomalies_cleared:
        save_json(CACHE_FILE, cache)
        print(f"Cleared {len(anomalies_cleared)} anomalies from cache.")
        
        # Esegui fetch_years.py per ricalcolarle con le nuove regole
        print("\nExecuting fetch_years.py to re-resolve cleared songs...")
        creation_flags = 0
        if sys.platform == 'win32':
            creation_flags = 0x08000000  # CREATE_NO_WINDOW
        res = subprocess.run([sys.executable, 'fetch_years.py'], capture_output=True, text=True, creationflags=creation_flags)
        print("Stdout:")
        print(res.stdout)
        if res.stderr:
            print("Stderr:")
            print(res.stderr)
            
        # Riesegui verify_years.py per generare il report aggiornato
        print("\nExecuting verify_years.py to update audit report...")
        subprocess.run([sys.executable, 'verify_years.py'], creationflags=creation_flags)
    else:
        print("No automatic anomalies found in cache (excluding manual overrides).")

if __name__ == "__main__":
    main()
