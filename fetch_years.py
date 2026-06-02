import json
import os
import re
import requests
import sys
import time
from collections import Counter

# Forza output non bufferizzato su Windows (evita log vuoti quando stdout è rediretto a file)
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
except TypeError:
    sys.stdout.reconfigure(line_buffering=True)

CACHE_FILE    = 'song_years_cache.json'
OVERRIDE_FILE = 'manual_years_override.json'
HISTORY_FILE  = 'radio_subasio_history.json'
DIVINA_FILE   = 'radio_divina_history.json'
MITOLOGY_FILE = 'radio_mitology_history.json'
NOSTALGIA_FILE= 'radio_nostalgia_history.json'
TOSCANA_FILE  = 'radio_toscana_history.json'
ITALIA_FILE   = 'radio_italia_history.json'
RDS_FILE      = 'radio_rds_history.json'
RTL1025_FILE  = 'radio_rtl1025_history.json'

def load_overrides():
    if os.path.exists(OVERRIDE_FILE):
        with open(OVERRIDE_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except Exception as e:
                print(f"Errore nel caricamento di {OVERRIDE_FILE}: {e}")
                return {}
    return {}

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)

def normalize_for_match(s):
    """Normalizza una stringa per il confronto: maiuscolo, rimuovi punteggiatura e parole accessorie."""
    s = s.upper()
    s = re.sub(r'\s*\(\d{4}\)\s*', '', s)          # Rimuovi anno tra parentesi
    s = re.sub(r'\bFEAT\.?\b|\bFT\.?\b|\bFEATURING\b', '', s, flags=re.I)
    s = re.sub(r'\s*[,&]\s*', ' ', s)               # Normalizza separatori artisti
    s = re.sub(r"[^\w\s]", ' ', s)                  # Rimuovi punteggiatura
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def build_radio_index(filepath):
    """
    Costruisce un indice {chiave_normalizzata: anno} da un file JSON di storia radio.
    Funziona con qualsiasi radio che includa l'anno nel formato: 'ARTISTA - TITOLO (ANNO)'
    """
    if not os.path.exists(filepath):
        return {}
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    index = {}
    year_re = re.compile(r'\((\d{4})\)\s*$')
    for item in data:
        song = item['song']
        m = year_re.search(song)
        if m:
            year = m.group(1)
            key = normalize_for_match(song)
            if key not in index:
                index[key] = year
    return index

def build_combined_index():
    """Indice combinato da tutte le radio che hanno anni nei titoli."""
    index = {}
    sources = [
        (HISTORY_FILE,   'Subasio'),
        (DIVINA_FILE,    'Divina'),
        (MITOLOGY_FILE,  'Mitology'),
        (NOSTALGIA_FILE, 'Nostalgia'),
        (TOSCANA_FILE,   'Toscana'),
        (ITALIA_FILE,    'Italia'),
        (RDS_FILE,       'RDS'),
        (RTL1025_FILE,   'RTL1025'),
    ]
    for filepath, label in sources:
        partial = build_radio_index(filepath)
        new_keys = 0
        for k, v in partial.items():
            if k not in index:
                index[k] = v
                new_keys += 1
        print(f"  Indice {label}: {len(partial)} brani ({new_keys} nuovi)", flush=True)
    return index

def get_year_from_radio_index(song_query, index):
    """Cerca l'anno nell'indice combinato delle radio. Nessuna chiamata API."""
    key = normalize_for_match(song_query)
    return index.get(key, "N/A")

def split_artist_title(song_query):
    """Separa artista e titolo dal formato 'ARTISTA - TITOLO'."""
    if " - " in song_query:
        parts = song_query.split(" - ", 1)
        return parts[0].strip(), parts[1].strip()
    return None, song_query.strip()

def extract_release_year_from_text(text):
    """
    Estrae l'anno di pubblicazione da un testo Wikipedia.
    Cerca anni vicino a parole chiave che indicano la data di uscita.
    Evita anni di nascita dell'artista o anni generici.
    """
    # Pattern: anno vicino a parole chiave di uscita (italiano e inglese)
    release_keywords_patterns = [
        # Italiano: "pubblicato nel 1985", "uscito il 3 marzo 1990"
        r'(?:pubblicat[oae]|uscit[oae]|rilasciat[oae]|estratt[oa]|incis[oa])[^.]{0,60}?\b(19[6-9]\d|20[0-2]\d)\b',
        # Inverso italiano: "nel 1985, pubblicato"
        r'\b(19[6-9]\d|20[0-2]\d)\b[^.]{0,60}?(?:pubblicat[oae]|uscit[oae]|rilasciat[oae])',
        # Inglese: "released in 1985", "published in 1990"
        r'(?:released|published|issued|recorded)[^.]{0,60}?\b(19[6-9]\d|20[0-2]\d)\b',
        # Inverso inglese: "in 1985, released"
        r'\b(19[6-9]\d|20[0-2]\d)\b[^.]{0,60}?(?:released|published|issued)',
        # "single del 1985", "album del 1990"
        r'(?:single|album|disco|brano)[^.]{0,60}?\b(19[6-9]\d|20[0-2]\d)\b',
        r'\b(19[6-9]\d|20[0-2]\d)\b[^.]{0,60}?(?:single|album|disco|brano)',
    ]

    found_years = []
    for pattern in release_keywords_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        found_years.extend(matches)

    if found_years:
        # Prendi il più antico tra quelli trovati (di solito è l'anno di uscita originale)
        valid_years = [y for y in found_years if 1960 <= int(y) <= 2026]
        if valid_years:
            return min(valid_years, key=lambda y: int(y))

    return None

def get_year_from_wikipedia(song_query):
    """
    Usa l'API di Wikipedia (IT e EN) per trovare l'anno di uscita della canzone.
    Cerca specificamente anni vicino a parole chiave di pubblicazione.
    """
    session = requests.Session()
    session.headers.update({'User-Agent': 'RadioMonitor/2.0 (radio@monitor.it)'})

    artist, title = split_artist_title(song_query)

    # Costruisce varie query di ricerca, dal più specifico al più generico
    if artist and title:
        search_queries_it = [
            f"{title} {artist}",
            f"{title} canzone",
            f"{title}",
        ]
        search_queries_en = [
            f"{title} {artist}",
            f"{title} song",
        ]
    else:
        search_queries_it = [f"{song_query} canzone", song_query]
        search_queries_en = [f"{song_query} song", song_query]

    # Prova prima Wikipedia italiana, poi inglese
    wikis = [
        ("https://it.wikipedia.org/w/api.php", search_queries_it),
        ("https://en.wikipedia.org/w/api.php", search_queries_en),
    ]

    for api_url, queries in wikis:
        for q in queries:
            try:
                search_params = {
                    "action": "query",
                    "format": "json",
                    "list": "search",
                    "srsearch": q,
                    "srlimit": 3  # Prende i primi 3 risultati
                }
                r = session.get(api_url, params=search_params, timeout=10)
                if r.status_code != 200:
                    continue
                data = r.json()
                search_results = data.get("query", {}).get("search", [])

                for result in search_results:
                    page_title = result["title"]

                    # Protezione: salta le pagine biografiche dell'artista
                    # (le bio contengono anni di nascita che vengono confusi con anni delle canzoni)
                    page_title_upper = page_title.upper()
                    title_words = [w.upper() for w in (title or song_query).split() if len(w) > 3]
                    title_in_page = any(w in page_title_upper for w in title_words)
                    if not title_in_page:
                        # La pagina non sembra parlare della canzone, salta
                        continue

                    content_params = {
                        "action": "query",
                        "format": "json",
                        "prop": "extracts",
                        "exintro": True,
                        "explaintext": True,
                        "titles": page_title
                    }
                    r2 = session.get(api_url, params=content_params, timeout=10)
                    pages = r2.json().get("query", {}).get("pages", {})

                    for page_id in pages:
                        text = pages[page_id].get("extract", "")
                        if not text:
                            continue

                        # Verifica che l'artista sia menzionato nella pagina (se presente) per evitare falsi positivi
                        if artist:
                            artist_words = [w.upper() for w in artist.split() if len(w) > 2]
                            artist_in_page = any(w in page_title_upper or w in text.upper() for w in artist_words)
                            if not artist_in_page:
                                continue

                        # Cerca anni vicino a parole chiave di release
                        year = extract_release_year_from_text(text)
                        if year:
                            return year

            except Exception as e:
                print(f"  Errore Wikipedia ({q}): {e}")

    return "N/A"

def get_year_from_genius(song_query):
    """Scraping leggero di Genius per trovare l'anno di uscita con validazione scoring."""
    artist, title = split_artist_title(song_query)
    if not artist or not title:
        return "N/A"

    search_url = f"https://genius.com/api/search/multi?q={song_query}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(search_url, headers=headers, timeout=10)
        sections = r.json().get("response", {}).get("sections", [])
        for section in sections:
            if section.get("type") == "song":
                hits = section.get("hits", [])
                for hit in hits[:3]:
                    result = hit.get("result", {})
                    g_title = result.get("title", "")
                    g_artist = result.get("primary_artist", {}).get("name", "")
                    
                    sa, st = _score_pair(g_artist, g_title, artist, title)
                    if sa >= 3 and st >= 3:
                        song_api_url = result["api_path"]
                        full_song_url = f"https://genius.com/api{song_api_url}"
                        r_song = requests.get(full_song_url, headers=headers, timeout=10)
                        song_data = r_song.json().get("response", {}).get("song", {})
                        
                        release_date = song_data.get("release_date_components")
                        if release_date and release_date.get("year"):
                            year = str(release_date["year"])
                            if 1960 <= int(year) <= 2026:
                                return year
                        # Fallback al campo release_date stringa
                        release_date_str = song_data.get("release_date")
                        if release_date_str:
                            y = release_date_str[:4]
                            if y.isdigit() and 1960 <= int(y) <= 2026:
                                return y
    except Exception as e:
        print(f"  Errore Genius per {song_query}: {e}")
    return "N/A"

def _norm(s):
    """Normalizza stringa: minuscolo, rimuovi accenti e punteggiatura."""
    import unicodedata as _ud
    s = (s or '').lower()
    s = _ud.normalize('NFD', s)
    s = ''.join(c for c in s if _ud.category(c) != 'Mn')
    s = re.sub(r'[^a-z0-9 ]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()

def _score_pair(r_artist, r_title, q_artist, q_title):
    """Punteggio artista+titolo (0-8 ciascuno). Stesso algoritmo di fetch_previews.py."""
    ra, rt = _norm(r_artist), _norm(r_title)
    al, tl = _norm(q_artist), _norm(q_title)
    sa = 8 if ra == al else (5 if (al in ra or ra in al) else
         sum(2 for w in al.split() if len(w) > 2 and w in ra))
    st = 8 if rt == tl else (5 if (tl in rt or rt in tl) else
         sum(2 for w in tl.split() if len(w) > 2 and w in rt))
    return sa, st

def get_year_from_itunes(song_query):
    """
    Usa l'API iTunes per cercare la canzone ed estrarre releaseDate.
    Usa lo stesso scoring robusto di fetch_previews.py:
    - entrambi artista E titolo devono avere score >= 3
    - sceglie il risultato col punteggio più alto, non il più vecchio
    """
    api_url = "https://itunes.apple.com/search"
    artist, title = split_artist_title(song_query)
    if not artist or not title:
        return "N/A"

    queries_to_try = [f"{artist} {title}", title]

    for query in queries_to_try:
        try:
            r = requests.get(api_url, params={
                "term": query, "media": "music", "entity": "song", "limit": 15
            }, timeout=10)
            results = r.json().get("results", [])

            best_score, best_year = -1, None
            for res in results:
                release_date = res.get("releaseDate", "")
                if not release_date:
                    continue
                yr = release_date[:4]
                if not yr.isdigit() or not (1960 <= int(yr) <= 2026):
                    continue
                sa, st = _score_pair(
                    res.get("artistName", ""), res.get("trackName", ""),
                    artist, title
                )
                # Entrambi devono superare soglia minima
                if sa >= 3 and st >= 3 and (sa + st) > best_score:
                    best_score = sa + st
                    best_year = yr
                    print(f"    iTunes match: {res.get('artistName')} – {res.get('trackName')} "
                          f"({yr}) score={sa}+{st}")

            if best_year:
                return best_year

        except Exception as e:
            print(f"  Errore API iTunes per {query}: {e}")

    return "N/A"

def get_mb_artist_name(rec):
    credits = rec.get("artist-credit", [])
    parts = []
    for c in credits:
        parts.append(c.get("name", ""))
        if "joinphrase" in c:
            parts.append(c["joinphrase"])
    return "".join(parts).strip()

def get_year_from_musicbrainz(song_query):
    """
    Usa l'API di MusicBrainz con query Lucene precisa artista+titolo e validazione scoring.
    """
    api_url = "https://musicbrainz.org/ws/2/recording"
    headers = {"User-Agent": "RadioMonitor/2.0 (mailto:radio@monitor.it)"}

    artist, title = split_artist_title(song_query)
    if not artist or not title:
        return "N/A"

    title_clean = re.sub(r'[+\-&|!(){}\[\]^"~*?:\\]', ' ', title).strip()
    artist_clean = re.sub(r'[+\-&|!(){}\[\]^"~*?:\\]', ' ', artist).strip()
    artist_clean = artist_clean.split(",")[0].strip()
    
    queries = [
        f'recording:"{title_clean}" AND artist:"{artist_clean}"',
        f'recording:"{title_clean}" AND artistname:"{artist_clean}"',
        f'{title_clean} {artist_clean}',
    ]

    best_score = -1
    best_year = "N/A"

    for query in queries:
        params = {
            "query": query,
            "fmt": "json",
            "limit": 10
        }
        try:
            r = requests.get(api_url, params=params, headers=headers, timeout=10)
            if r.status_code != 200:
                continue
            recordings = r.json().get("recordings", [])

            for rec in recordings:
                rec_artist = get_mb_artist_name(rec)
                rec_title = rec.get("title", "")
                sa, st = _score_pair(rec_artist, rec_title, artist, title)
                
                # Entrambi devono superare la soglia minima
                if sa >= 3 and st >= 3:
                    years = []
                    for rel in rec.get("releases", []):
                        date = rel.get("date", "")
                        if date and len(date) >= 4:
                            y = date[:4]
                            if y.isdigit() and 1960 <= int(y) <= 2026:
                                years.append(int(y))
                    if years:
                        min_yr = str(min(years))
                        score = sa + st
                        if score > best_score:
                            best_score = score
                            best_year = min_yr
                        elif score == best_score:
                            if best_year == "N/A" or int(min_yr) < int(best_year):
                                best_year = min_yr
            
            # Se abbiamo trovato un buon match a questo livello, non facciamo fallback a query più lasche
            if best_year != "N/A":
                return best_year

        except Exception as e:
            print(f"  Errore MusicBrainz per {query}: {e}")

        time.sleep(0.5)  # Rate limit MusicBrainz

    return best_year

def is_valid_year_for_song(song, year):
    """
    Controlla se l'anno è compatibile con il debutto dell'artista.
    Usa la stessa logica robusta di verify_years.py per evitare falsi positivi.
    """
    if not year or year == "N/A":
        return False
    if not year.isdigit():
        return False
    y_int = int(year)
    
    # Mappa dei debutti allineata a verify_years.py
    artist_debut_map = {
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
    
    artist, title = split_artist_title(song)
    artist_upper = artist.upper() if artist else song.upper()
    
    for a_key, debut_y in artist_debut_map.items():
        if a_key == 'ANNALISA' and 'ANNALISA MINETTI' in artist_upper:
            continue
        if a_key == 'OLLY' and 'OLLY MURS' in artist_upper:
            continue
            
        # Match rigoroso con word boundaries per evitare falsi positivi
        pattern = r'\b' + re.escape(a_key) + r'\b'
        if re.search(pattern, artist_upper):
            if y_int < debut_y:
                print(f"  [SCARTATO CON VETO] Anno {year} impossibile per {a_key} (debutto {debut_y})")
                return False
    return True

def main():
    cache = load_cache()
    overrides = load_overrides()
    # Applica preventivamente gli override alla cache
    for song, yr in overrides.items():
        cache[song] = yr
    save_cache(cache)
    
    history_files = [
        HISTORY_FILE,
        DIVINA_FILE,
        MITOLOGY_FILE,
        NOSTALGIA_FILE,
        TOSCANA_FILE,
        ITALIA_FILE,
        RDS_FILE,
        RTL1025_FILE
    ]

    songs_to_process = []
    for filepath in history_files:
        if not os.path.exists(filepath):
            print(f"File {filepath} non trovato, lo salto.", flush=True)
            continue
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                songs_to_process.extend([item['song'] for item in data])
        except Exception as e:
            print(f"Errore nel caricamento di {filepath}: {e}", flush=True)

    # Carica indice combinato da tutte le radio con anni nei titoli
    print("Costruzione indice radio locali...", flush=True)
    radio_index = build_combined_index()
    print(f"Indice combinato: {len(radio_index)} brani con anno", flush=True)

    # Rimuovi l'anno dal titolo se presente (es. "Canzone (1985)")
    songs_clean = []
    for s in songs_to_process:
        # Normalizza: rimuovi eventuale anno già nel titolo
        s_no_year = re.sub(r'\s*\(\d{4}\)\s*$', '', s).strip()
        songs_clean.append(s_no_year)

    song_counts = Counter(songs_clean)

    # Parole chiave da escludere (non sono canzoni)
    exclude_keywords = [
        'PROMO', 'WEBRADIO', 'SPOT', 'IDENT', 'GINGLE', 'JINGLE',
        'PUBBLICITA', 'RADIO SUBASIO', 'ORA ESATTA', 'STAZIONE',
        'SRS ', 'SPONSOR',
        # Nuove stazioni radio
        'RADIO DIVINA', 'RADIO MITOLOGY', 'RADIO NOSTALGIA', 'RADIO TOSCANA',
        'RADIO ITALIA', 'RDS', 'RTL 102.5', 'RTL1025',
        # Parole chiave dei messaggi e del servizio
        'VOCALE', 'WHATSAPP', 'SMS', 'CHIAMA', 'DIRETTA', 'METEO',
        'TRAFFICO', 'NOTIZIARIO', '338 63 60 114', '3386360114',
        'COMING SOON', 'CINEMA', 'PREVISIONI'
    ]

    all_songs = []
    for s, _ in song_counts.most_common():
        # Escludi parole chiave di servizio
        if any(kw in s.upper() for kw in exclude_keywords):
            cache[s] = "N/A"
            continue
        all_songs.append(s)

    # ── PASSAGGIO 1: cross-radio su TUTTI i brani (sovrascrive cache se trova anno più affidabile)
    # L'anno embedded nelle altre radio è diretto dal dato trasmesso → fonte più affidabile
    radio_resolved = 0
    for song in all_songs:
        if song in overrides:
            continue
        year = get_year_from_radio_index(song, radio_index)
        if year != "N/A":
            if cache.get(song) != year:
                if cache.get(song) and cache.get(song) != "N/A":
                    print(f"  [CORRETTO] {song}: {cache[song]} → {year} (cross-radio)", flush=True)
                cache[song] = year
                radio_resolved += 1
    if radio_resolved:
        save_cache(cache)
        print(f"  Cross-radio: aggiornati {radio_resolved} brani.", flush=True)

    # ── PASSAGGIO 2: API esterne solo per i brani ancora senza anno ──────────
    import random
    new_songs = [s for s in all_songs if s not in overrides and s not in cache]
    na_songs = [s for s in all_songs if s not in overrides and cache.get(s) == "N/A"]
    
    # Mescola i brani N/A per evitare che blocchino la coda deterministica
    random.shuffle(na_songs)
    
    to_search = new_songs + na_songs
    
    # Limita le ricerche API per questa esecuzione per evitare rate-limiting e completare in tempi ragionevoli
    MAX_API_SEARCHES = 100
    print(f"Brani nuovi (priorità): {len(new_songs)} | Brani N/A in coda mescolati: {len(na_songs)}", flush=True)
    print(f"Brani ancora senza anno totali: {len(to_search)}", flush=True)
    if len(to_search) > MAX_API_SEARCHES:
        print(f"Limito la ricerca API a un massimo di {MAX_API_SEARCHES} brani per questa sessione.", flush=True)
        to_search = to_search[:MAX_API_SEARCHES]

    # ── PASSAGGIO 2: API esterne per i brani non trovati cross-radio ──────────
    processed = 0
    for song in to_search:
        print(f"Ricerca: {song}...", flush=True)

        # Sequenza a cascata: MusicBrainz -> iTunes -> Genius -> Wikipedia
        year = "N/A"

        # 1. Prova MusicBrainz
        candidate = get_year_from_musicbrainz(song)
        if candidate != "N/A":
            if is_valid_year_for_song(song, candidate):
                year = candidate
            else:
                print(f"  MusicBrainz: anno non valido ({candidate}), provo iTunes...")
        
        # 2. Prova iTunes se necessario
        if year == "N/A":
            candidate = get_year_from_itunes(song)
            if candidate != "N/A":
                if is_valid_year_for_song(song, candidate):
                    year = candidate
                else:
                    print(f"  iTunes: anno non valido ({candidate}), provo Genius...")

        # 3. Prova Genius se necessario
        if year == "N/A":
            candidate = get_year_from_genius(song)
            if candidate != "N/A":
                if is_valid_year_for_song(song, candidate):
                    year = candidate
                else:
                    print(f"  Genius: anno non valido ({candidate}), provo Wikipedia...")

        # 4. Prova Wikipedia se necessario
        if year == "N/A":
            candidate = get_year_from_wikipedia(song)
            if candidate != "N/A":
                if is_valid_year_for_song(song, candidate):
                    year = candidate
                else:
                    print(f"  Wikipedia: anno non valido ({candidate}).")

        # Memorizza nella cache
        cache[song] = year
        if year != "N/A":
            print(f"  -> Trovato e validato: {year}")
        else:
            print("  -> Non trovato (nessuna fonte valida o anno scartato).")

        processed += 1
        time.sleep(1.5)  # Rispetto per le API

        if processed % 5 == 0:
            save_cache(cache)

    save_cache(cache)
    print(f"\nFine sessione. Processati {processed} brani.", flush=True)

if __name__ == "__main__":
    main()
