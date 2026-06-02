import json
import os
import re
import sys
import time
import subprocess
import urllib.parse
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# Ensure stdout is unbuffered for real-time logging
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
except TypeError:
    sys.stdout.reconfigure(line_buffering=True)

CACHE_FILE = 'song_radiodates_cache.json'
OVERRIDE_FILE = 'manual_radiodates_override.json'
YEARS_CACHE_FILE = 'song_years_cache.json'

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

# Service/promo keywords to exclude
exclude_keywords = [
    'PROMO', 'WEBRADIO', 'SPOT', 'IDENT', 'GINGLE', 'JINGLE',
    'PUBBLICITA', 'RADIO SUBASIO', 'ORA ESATTA', 'STAZIONE',
    'SRS ', 'SPONSOR',
    'RADIO DIVINA', 'RADIO MITOLOGY', 'RADIO NOSTALGIA', 'RADIO TOSCANA',
    'RADIO ITALIA', 'RDS', 'RTL 102.5', 'RTL1025',
    'VOCALE', 'WHATSAPP', 'SMS', 'CHIAMA', 'DIRETTA', 'METEO',
    'TRAFFICO', 'NOTIZIARIO', '338 63 60 114', '3386360114',
    'COMING SOON', 'CINEMA', 'PREVISIONI'
]

def load_json(path, default_factory=dict):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except Exception as e:
                print(f"Error loading {path}: {e}")
                return default_factory()
    return default_factory()

def save_json(data, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def split_artist_title(song):
    if " - " in song:
        parts = song.split(" - ", 1)
        return parts[0].strip(), parts[1].strip()
    return "Unknown", song

def clean_artist_for_search(artist):
    # Extract first main artist
    artist = re.split(r'\bFEAT\.?\b|\bFT\.?\b|\bFEATURING\b|\bWITH\b', artist, flags=re.I)[0].strip()
    artist = re.split(r'[,&;]', artist)[0].strip()
    artist = re.sub(r'\s+', ' ', artist)
    return artist

def normalize_string(s):
    if not s:
        return ""
    s = s.lower()
    import unicodedata
    s = unicodedata.normalize('NFD', s)
    s = "".join(c for c in s if unicodedata.category(c) != 'Mn')
    s = re.sub(r'\(.*?\)', '', s)
    s = re.sub(r'\b(feat|ft|featuring|vs|pres|present|with)\b', '', s)
    s = re.sub(r'[^a-z0-9\s]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()

def match_score(q_art, q_tit, r_art, r_tit):
    n_q_art = normalize_string(q_art)
    n_q_tit = normalize_string(q_tit)
    n_r_art = normalize_string(r_art)
    n_r_tit = normalize_string(r_tit)
    
    if n_q_art == n_r_art and n_q_tit == n_r_tit:
        return 100
    if n_q_tit == n_r_tit:
        if n_q_art in n_r_art or n_r_art in n_q_art:
            return 95
        q_art_tokens = set(n_q_art.split())
        r_art_tokens = set(n_r_art.split())
        overlap = q_art_tokens.intersection(r_art_tokens)
        if len(overlap) > 0:
            return 85 + len(overlap)
    if (n_q_art in n_r_art or n_r_art in n_q_art) and (n_q_tit in n_r_tit or n_r_tit in n_q_tit):
        return 80
    return 0

def format_date(date_str):
    if not date_str or date_str == "None":
        return "N/A"
    date_str = date_str.strip()
    # YYYY-MM-DD
    m = re.match(r'^(\d{4})-(\d{2})-(\d{2})$', date_str)
    if m:
        return f"{m.group(3)}/{m.group(2)}/{m.group(1)}"
    # DD/MM/YYYY
    m = re.match(r'^(\d{2})/(\d{2})/(\d{4})$', date_str)
    if m:
        return f"{m.group(1)}/{m.group(2)}/{m.group(3)}"
    return "N/A"

def fetch_earone_page(url):
    """Fetches a page from EarOne using curl.exe to handle HTTP 103 Early Hints safely."""
    try:
        result = subprocess.run(
            ["curl.exe", "-s", "-L", "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", url],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=20
        )
        if result.returncode == 0:
            return result.stdout
        else:
            print(f"  [ERROR] Curl execution failed with code {result.returncode}")
            return ""
    except Exception as e:
        print(f"  [ERROR] Subprocess curl failed: {e}")
        return ""

def parse_pageProps_from_html(html):
    if not html:
        return {}
    soup = BeautifulSoup(html, 'html.parser')
    large_script = None
    for s in soup.find_all('script'):
        text = s.string or ''
        if len(text) > 1000 and 'pageProps' in text:
            large_script = text
            break
    if large_script:
        try:
            return json.loads(large_script).get('pageProps', {})
        except Exception as e:
            print(f"  [ERROR] Failed to parse script JSON: {e}")
            return {}
    return {}

def search_earone(query):
    """Searches EarOne's database for a query term."""
    encoded_query = urllib.parse.quote(query)
    url = f"https://www.earone.it/radio-date/all?search={encoded_query}"
    print(f"  Querying: {url} ...")
    html = fetch_earone_page(url)
    page_props = parse_pageProps_from_html(html)
    return page_props.get('filteredRadioDate', [])

def search_earone_via_web(song):
    """
    Cerca il brano su Yahoo e Bing (utilizzando curl.exe per aggirare i blocchi delle richieste standard)
    aggiungendo "earone" per trovare direttamente il link all'articolo di EarOne
    ed estrarre la data di pubblicazione.
    """
    artist, title = split_artist_title(song)
    query = f"{artist} {title} earone"
    print(f"  [WEB SEARCH] Cerca su motori di ricerca: '{query}'...")
    encoded_query = urllib.parse.quote(query)
    
    # 1. Prova Yahoo Mobile (estremamente efficace e indicizzato benissimo)
    url_yahoo = f"https://search.yahoo.com/search?p={encoded_query}"
    # 2. Prova Bing Mobile (eccellente fallback)
    url_bing = f"https://www.bing.com/search?q={encoded_query}"
    
    urls_to_try = [
        ("Yahoo", url_yahoo, "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"),
        ("Bing", url_bing, "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1")
    ]
    
    for engine, url, ua in urls_to_try:
        try:
            print(f"    Interrogazione {engine}: {url} ...")
            result = subprocess.run(
                ["curl.exe", "-s", "-L", "-A", ua, url],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=15
            )
            
            if result.returncode != 0 or not result.stdout or len(result.stdout) < 5000:
                print(f"      -> {engine} vuoto, troppo corto o errore (code {result.returncode}). Provo il prossimo...")
                continue
                
            soup = BeautifulSoup(result.stdout, 'html.parser')
            
            # Cerca i link ai post di EarOne
            for a in soup.find_all('a', href=True):
                href = a['href']
                
                # Decodifica link Yahoo (es. /RU=...)
                if '/RU=' in href:
                    match = re.search(r'/RU=([^/]+)', href)
                    if match:
                        href = urllib.parse.unquote(match.group(1))
                    else:
                        try:
                            ru_part = href.split('/RU=')[1].split('/')[0]
                            href = urllib.parse.unquote(ru_part)
                        except:
                            pass
                            
                # Decodifica click tracking di Bing (es. /ck/a?...)
                elif '/ck/a?' in href:
                    parsed = urllib.parse.urlparse(href)
                    query_params = urllib.parse.parse_qs(parsed.query)
                    if 'u' in query_params:
                        u_val = query_params['u'][0]
                        if u_val.startswith('a1'):
                            import base64
                            base64_str = u_val[2:]
                            base64_str = base64_str.replace('-', '+').replace('_', '/')
                            padding = len(base64_str) % 4
                            if padding > 0:
                                base64_str += '=' * (4 - padding)
                            try:
                                decoded_bytes = base64.b64decode(base64_str.encode('utf-8'), validate=False)
                                href = decoded_bytes.decode('utf-8', errors='ignore')
                            except:
                                pass
                                
                if 'earone.it' in href or 'earone.com' in href:
                    print(f"      -> Trovato URL EarOne: {href}")
                    
                    # 1. Prova ad estrarre la data direttamente dall'URL (es. ...radio-date-23-01-2026)
                    match = re.search(r'(?<!\d)(\d{2})[-_](\d{2})[-_](\d{4})(?!\d)', href)
                    if match:
                        day, month, year = match.group(1), match.group(2), match.group(3)
                        if 2010 <= int(year) <= 2026:
                            found_date = f"{day}/{month}/{year}"
                            print(f"      [WEB SUCCESS] Estratta data da URL: {found_date}")
                            return found_date
                            
                    match_iso = re.search(r'(?<!\d)(\d{4})[-_](\d{2})[-_](\d{2})(?!\d)', href)
                    if match_iso:
                        year, month, day = match_iso.group(1), match_iso.group(2), match_iso.group(3)
                        if 2010 <= int(year) <= 2026:
                            found_date = f"{day}/{month}/{year}"
                            print(f"      [WEB SUCCESS] Estratta data da URL (ISO): {found_date}")
                            return found_date
                            
                    # 2. Se non presente nell'URL, scarica la pagina dell'articolo per estrarre la data
                    print(f"      Scaricamento contenuto articolo per estrarre la data...")
                    art_html = fetch_earone_page(href)
                    if art_html:
                        art_soup = BeautifulSoup(art_html, 'html.parser')
                        page_text = art_soup.get_text()
                        
                        # Cerca DD/MM/YYYY o DD-MM-YYYY (supportando anche l'assenza di word boundaries \b)
                        match_text = re.search(r'(?<!\d)(\d{2})/(\d{2})/(\d{4})(?!\d)', page_text)
                        if match_text:
                            day, month, year = match_text.group(1), match_text.group(2), match_text.group(3)
                            if 2010 <= int(year) <= 2026:
                                found_date = f"{day}/{month}/{year}"
                                print(f"      [WEB SUCCESS] Estratta data da testo: {found_date}")
                                return found_date
                                
                        match_text_dash = re.search(r'(?<!\d)(\d{2})-(\d{2})-(\d{4})(?!\d)', page_text)
                        if match_text_dash:
                            day, month, year = match_text_dash.group(1), match_text_dash.group(2), match_text_dash.group(3)
                            if 2010 <= int(year) <= 2026:
                                found_date = f"{day}/{month}/{year}"
                                print(f"      [WEB SUCCESS] Estratta data da testo (trattini): {found_date}")
                                return found_date
                                
                        # Cerca formato con mese in italiano (es. 23 gennaio 2026)
                        months_it = {
                            'gennaio': '01', 'febbraio': '02', 'marzo': '03', 'aprile': '04',
                            'maggio': '05', 'giugno': '06', 'luglio': '07', 'agosto': '08',
                            'settembre': '09', 'ottobre': '10', 'novembre': '11', 'dicembre': '12'
                        }
                        months_pattern = '|'.join(months_it.keys())
                        match_it = re.search(r'(?<!\d)(\d{1,2})\s+(' + months_pattern + r')\s+(\d{4})(?!\d)', page_text, re.IGNORECASE)
                        if match_it:
                            day = match_it.group(1).zfill(2)
                            month = months_it[match_it.group(2).lower()]
                            year = match_it.group(3)
                            if 2010 <= int(year) <= 2026:
                                found_date = f"{day}/{month}/{year}"
                                print(f"      [WEB SUCCESS] Estratta data da testo (italiano): {found_date}")
                                return found_date
                                
            time.sleep(2)  # Rispetto per i motori di ricerca
        except Exception as e:
            print(f"      [WEB ERROR] Errore durante interrogazione {engine}: {e}")
            
    return "N/A"

def main():
    start_time = time.time()
    
    # 1. Load files
    cache = load_json(CACHE_FILE)
    overrides = load_json(OVERRIDE_FILE)
    years_cache = load_json(YEARS_CACHE_FILE)
    
    # Create overrides file if it doesn't exist
    if not os.path.exists(OVERRIDE_FILE):
        save_json({}, OVERRIDE_FILE)
        print(f"Created empty manual overrides file: {OVERRIDE_FILE}")

    # Proactively merge manual overrides into the cache
    for song, rd in overrides.items():
        cache[song] = rd
    
    # 2. Extract unique songs and their latest play date from histories
    print("Aggregating unique songs and latest play dates from histories...", flush=True)
    song_latest_date = {}
    
    # We parse DD.MM dates relative to current date (e.g. 2026-06-02)
    now_dt = datetime.now()
    curr_year = now_dt.year
    curr_month = now_dt.month

    def parse_dm_date(dm_str):
        try:
            d, m = map(int, dm_str.split('.'))
            # Se il mese del passaggio è maggiore del mese corrente, assumiamo che si riferisca all'anno precedente
            y = curr_year if m <= curr_month else curr_year - 1
            return datetime(y, m, d)
        except Exception:
            return None

    for filename in HISTORY_FILES:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    for item in data:
                        song = item['song']
                        dt_str = item.get('date', '')
                        dt = parse_dm_date(dt_str)
                        if not dt:
                            # Data di fallback se il parsing fallisce
                            dt = datetime(2000, 1, 1)
                        if song not in song_latest_date or dt > song_latest_date[song]:
                            song_latest_date[song] = dt
                except Exception as e:
                    print(f"Error loading history {filename}: {e}")
        else:
            print(f"History file {filename} not found, skipping.")
            
    # Clean unique songs and keep their latest play date
    clean_songs = {}
    for s, last_dt in song_latest_date.items():
        s_no_year = re.sub(r'\s*\(\d{4}\)\s*$', '', s).strip()
        if not any(kw in s_no_year.upper() for kw in exclude_keywords):
            if s_no_year not in clean_songs or last_dt > clean_songs[s_no_year]:
                clean_songs[s_no_year] = last_dt
            
    print(f"Total aggregated unique songs (filtered): {len(clean_songs)}")
    
    # 3. Apply Pre-2010 N/A optimization
    print("Applying Pre-2010 N/A optimization using years cache...", flush=True)
    optimized_count = 0
    for song in clean_songs:
        if song in overrides:
            continue
        if song in cache:
            continue
            
        yr = years_cache.get(song)
        if yr and yr != "N/A":
            try:
                if int(yr) < 2010:
                    cache[song] = "N/A"
                    optimized_count += 1
            except ValueError:
                pass
                
    if optimized_count > 0:
        save_json(cache, CACHE_FILE)
        print(f"  Optimized {optimized_count} songs as N/A without any network requests!")

    # 4. Filter active songs needing scraping
    # Consentiamo di ri-cercare le radio date dei brani recenti (anno >= 2025)
    # o con anno mancante ("N/A") ma trasmessi di recente (negli ultimi 30 giorni) che sono attualmente contrassegnati come "N/A" o "N/D" in cache,
    # poiché la data potrebbe essere stata pubblicata su EarOne solo in un secondo momento.
    # Escludiamo sempre qualsiasi brano presente in overrides per non sovrascrivere le scelte dell'utente.
    import random
    new_songs = []
    na_songs = []
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    for s, last_played in clean_songs.items():
        if s in overrides:
            continue  # Salta se presente negli override manuali
            
        if s not in cache:
            new_songs.append(s)
        elif cache[s] in ["N/A", "N/D"]:
            yr = years_cache.get(s, "N/A")
            is_recent_year = False
            try:
                if yr != "N/A" and int(yr) >= 2025:
                    is_recent_year = True
            except ValueError:
                pass
                
            is_recently_played = (last_played >= thirty_days_ago)
            
            if is_recent_year or (yr == "N/A" and is_recently_played):
                na_songs.append(s)
                
    # Mescola i brani N/A/ND per garantire un ricontrollo equo e non bloccante
    random.shuffle(na_songs)
    active_songs = new_songs + na_songs
    print(f"Brani nuovi (priorità): {len(new_songs)} | Brani N/A in coda mescolati: {len(na_songs)}")
    print(f"Songs remaining to process: {len(active_songs)}")
    
    if len(active_songs) == 0:
        print("All songs are already cached or optimized. Finished!")
        return
        
    # Group active songs by primary cleaned artist name
    artist_to_songs = {}
    for s in active_songs:
        art, tit = split_artist_title(s)
        clean_art = clean_artist_for_search(art)
        if clean_art not in artist_to_songs:
            artist_to_songs[clean_art] = []
        artist_to_songs[clean_art].append(s)
        
    print(f"Active songs grouped into {len(artist_to_songs)} unique artists.")
    
    # Sort artists by number of active songs (descending) to optimize hits
    sorted_artists = sorted(artist_to_songs.items(), key=lambda x: len(x[1]), reverse=True)
    
    # Set a request cap to fit in standard agent runtimes
    MAX_REQUESTS = 250
    requests_made = 0
    resolved_count = 0
    
    print(f"Starting EarOne scraping (Max requests: {MAX_REQUESTS}, sleeping 1.5s between requests)...", flush=True)
    
    # Process multi-song artists first (high efficiency)
    for artist, song_list in sorted_artists:
        if requests_made >= MAX_REQUESTS:
            print("Reached request limit cap.")
            break
            
        print(f"\n[{requests_made+1}] Processing artist: '{artist}' ({len(song_list)} active songs in DB)")
        
        # Search EarOne for this artist
        results = search_earone(artist)
        requests_made += 1
        
        # Match results against all active songs for this artist
        artist_resolved = 0
        for song_db in song_list:
            db_art, db_tit = split_artist_title(song_db)
            
            # Find best match in results
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
                raw_date = best_item.get('radioDate')
                formatted = format_date(raw_date)
                cache[song_db] = formatted
                resolved_count += 1
                artist_resolved += 1
                print(f"  -> Match Found: '{song_db}' -> {formatted} (Score: {best_score})")
            else:
                # We will mark it as N/A if it is a single-song artist search, but for multi-song artists,
                # maybe they just weren't in this list. We'll leave them to search by title later,
                # or if this is the final check, mark as N/A. Let's see.
                pass
                
        # For any song of this artist that WAS NOT resolved, let's try specific fallbacks
        if len(results) == 0:
            # If the artist has no matches at all, try internal title-only search first, then web search fallback!
            for song_db in song_list:
                db_art, db_tit = split_artist_title(song_db)
                print(f"  Artist '{artist}' has no matches. Trying internal title-only search: '{db_tit}'")
                title_results = search_earone(db_tit)
                requests_made += 1
                
                best_score = 0
                best_item = None
                for res in title_results:
                    res_song = res.get('song', {})
                    res_artists = ", ".join([a.get('name') for a in res_song.get('tracks', [{}])[0].get('artists', [])]) if res_song.get('tracks') else "Unknown"
                    res_title = res_song.get('title', '')
                    
                    score = match_score(db_art, db_tit, res_artists, res_title)
                    if score > best_score:
                        best_score = score
                        best_item = res
                        
                if best_item and best_score >= 80:
                    formatted = format_date(best_item.get('radioDate'))
                    cache[song_db] = formatted
                    resolved_count += 1
                    print(f"  -> Found title-only match: '{song_db}' -> {formatted} (Score: {best_score})")
                else:
                    web_date = search_earone_via_web(song_db)
                    if web_date != "N/A":
                        cache[song_db] = web_date
                        resolved_count += 1
                        print(f"  -> Found via Web Fallback: '{song_db}' -> {web_date}")
                    else:
                        cache[song_db] = "N/A"
                        resolved_count += 1
                        print(f"  -> No records on EarOne. Marking as N/A: '{song_db}'")
                artist_resolved += 1
                time.sleep(1.5)
        else:
            # If the artist has matches, but some songs were not found:
            # Let's do a targeted search for the specific song titles of unresolved ones if they are high priority
            for song_db in song_list:
                if song_db not in cache or cache[song_db] == "N/A":
                    if requests_made >= MAX_REQUESTS:
                        break
                    print(f"  Targeted query for song: '{song_db}'")
                    db_art, db_tit = split_artist_title(song_db)
                    song_results = search_earone(f"{db_art} {db_tit}")
                    requests_made += 1
                    
                    best_score = 0
                    best_item = None
                    for res in song_results:
                        res_song = res.get('song', {})
                        res_artists = ", ".join([a.get('name') for a in res_song.get('tracks', [{}])[0].get('artists', [])]) if res_song.get('tracks') else "Unknown"
                        res_title = res_song.get('title', '')
                        
                        score = match_score(db_art, db_tit, res_artists, res_title)
                        if score > best_score:
                            best_score = score
                            best_item = res
                            
                    if best_item and best_score >= 80:
                        formatted = format_date(best_item.get('radioDate'))
                        cache[song_db] = formatted
                        resolved_count += 1
                        print(f"    -> Found targeted match: '{song_db}' -> {formatted} (Score: {best_score})")
                    else:
                        print(f"    Targeted query failed. Trying internal title-only search: '{db_tit}'")
                        title_results = search_earone(db_tit)
                        requests_made += 1
                        
                        best_score = 0
                        best_item = None
                        for res in title_results:
                            res_song = res.get('song', {})
                            res_artists = ", ".join([a.get('name') for a in res_song.get('tracks', [{}])[0].get('artists', [])]) if res_song.get('tracks') else "Unknown"
                            res_title = res_song.get('title', '')
                            
                            score = match_score(db_art, db_tit, res_artists, res_title)
                            if score > best_score:
                                best_score = score
                                best_item = res
                                
                        if best_item and best_score >= 80:
                            formatted = format_date(best_item.get('radioDate'))
                            cache[song_db] = formatted
                            resolved_count += 1
                            print(f"    -> Found title-only match: '{song_db}' -> {formatted} (Score: {best_score})")
                        else:
                            web_date = search_earone_via_web(song_db)
                            if web_date != "N/A":
                                cache[song_db] = web_date
                                resolved_count += 1
                                print(f"    -> Found via Web Fallback: '{song_db}' -> {web_date}")
                            else:
                                cache[song_db] = "N/A"
                                resolved_count += 1
                                print(f"    -> Not found on EarOne. Marking as N/A: '{song_db}'")
                    
                    time.sleep(1.5)
                    
        # Periodic save
        save_json(cache, CACHE_FILE)
        time.sleep(1.5)
        
    save_json(cache, CACHE_FILE)
    
    # 5. Output stats
    end_time = time.time()
    elapsed = round(end_time - start_time, 2)
    
    total_songs = len(clean_songs)
    cached_songs = len(cache)
    with_date = sum(1 for v in cache.values() if v != "N/A")
    na_songs = sum(1 for v in cache.values() if v == "N/A")
    
    print("\n" + "="*50)
    print("             SCRAPING WORKFLOW COMPLETE")
    print("="*50)
    print(f"Total unique songs in histories: {total_songs}")
    print(f"Total songs now resolved in cache: {cached_songs} ({cached_songs/total_songs*100:.1f}%)")
    print(f"  - Songs with a matched Radio Date: {with_date}")
    print(f"  - Songs marked as N/A (no radio date): {na_songs}")
    print(f"Total active requests made this run: {requests_made}")
    print(f"Total songs resolved this run: {resolved_count}")
    print(f"Execution time: {elapsed} seconds")
    print("="*50)

if __name__ == "__main__":
    main()
