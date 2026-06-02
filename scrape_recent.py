import json
import os
import re
import sys
import time
import subprocess
import urllib.parse
from bs4 import BeautifulSoup

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
    
    # 1. Prova Yahoo Mobile
    url_yahoo = f"https://search.yahoo.com/search?p={encoded_query}"
    # 2. Prova Bing Mobile
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
                print(f"      -> {engine} vuoto, troppo corto o errore. Provo il prossimo...")
                continue
                
            soup = BeautifulSoup(result.stdout, 'html.parser')
            for a in soup.find_all('a', href=True):
                href = a['href']
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
                            
                    print(f"      Scaricamento contenuto articolo per estrarre la data...")
                    art_html = fetch_earone_page(href)
                    if art_html:
                        art_soup = BeautifulSoup(art_html, 'html.parser')
                        page_text = art_soup.get_text()
                        
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
                                
            time.sleep(2)
        except Exception as e:
            print(f"      [WEB ERROR] Errore durante interrogazione {engine}: {e}")
    return "N/A"

def main():
    start_time = time.time()
    
    # Load files
    cache = load_json(CACHE_FILE)
    overrides = load_json(OVERRIDE_FILE)
    years_cache = load_json(YEARS_CACHE_FILE)
    
    # Integrate overrides
    for song, rd in overrides.items():
        cache[song] = rd
        
    # Get histories and count occurrences
    print("Loading histories to identify candidate songs...", flush=True)
    song_counts = {}
    for filename in HISTORY_FILES:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    song = item['song']
                    song_counts[song] = song_counts.get(song, 0) + 1
                    
    # Clean and filter candidate songs
    candidates = []
    for song, count in song_counts.items():
        song_clean = re.sub(r'\s*\(\d{4}\)\s*$', '', song).strip()
        if any(kw in song_clean.upper() for kw in exclude_keywords):
            continue
            
        # Check if already resolved in cache with a valid date
        cached_rd = cache.get(song_clean)
        if cached_rd and cached_rd not in ['N/A', 'N/D']:
            continue
            
        yr = years_cache.get(song_clean, 'UNKNOWN')
        
        # We target:
        # - Any song with year 2024, 2025, 2026 (even if cached as N/A/N/D, we re-evaluate)
        # - Any UNKNOWN year song that has count >= 2
        is_recent = yr in ['2024', '2025', '2026']
        is_unknown_popular = (yr == 'UNKNOWN' and count >= 2)
        
        if is_recent or is_unknown_popular:
            candidates.append({
                'song': song_clean,
                'year': yr,
                'count': count,
                'cached_rd': cached_rd
            })
            
    print(f"Total candidates matching criteria: {len(candidates)}")
    
    # Group candidates by artist
    artist_groups = {}
    for c in candidates:
        art, tit = split_artist_title(c['song'])
        clean_art = clean_artist_for_search(art)
        if clean_art not in artist_groups:
            artist_groups[clean_art] = []
        artist_groups[clean_art].append(c)
        
    print(f"Grouped into {len(artist_groups)} unique artists")
    
    # Sort artist groups by count of candidate songs (highest first)
    sorted_artists = sorted(artist_groups.items(), key=lambda x: (sum(item['count'] for item in x[1])), reverse=True)
    
    # We will run up to 200 requests to cover the most popular ones first
    MAX_REQUESTS = 200
    requests_made = 0
    resolved_count = 0
    
    print(f"Starting scraping (Max requests: {MAX_REQUESTS})...", flush=True)
    
    for artist, song_list in sorted_artists:
        if requests_made >= MAX_REQUESTS:
            print("Reached request limit.")
            break
            
        # Show what we are querying
        total_plays = sum(item['count'] for item in song_list)
        print(f"\n[{requests_made+1}] Querying '{artist}' (Songs to resolve: {len(song_list)}, total plays: {total_plays})")
        
        results = search_earone(artist)
        requests_made += 1
        
        # Match results against our songs
        resolved_any = False
        for c in song_list:
            song_db = c['song']
            db_art, db_tit = split_artist_title(song_db)
            
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
                cache[song_db] = formatted
                resolved_count += 1
                resolved_any = True
                print(f"  -> MATCH: '{song_db}' -> {formatted} (Score: {best_score})")
            else:
                # If the artist has some matches, but this specific song wasn't found,
                # let's try a direct query for this song if it's from 2025 or 2026 and has high frequency
                if c['year'] in ['2025', '2026'] and c['count'] >= 2 and requests_made < MAX_REQUESTS:
                    print(f"  -> Targeted query for song: '{song_db}'")
                    time.sleep(1.5)
                    song_results = search_earone(f"{db_art} {db_tit}")
                    requests_made += 1
                    
                    s_best_score = 0
                    s_best_item = None
                    for res in song_results:
                        res_song = res.get('song', {})
                        res_artists = ", ".join([a.get('name') for a in res_song.get('tracks', [{}])[0].get('artists', [])]) if res_song.get('tracks') else "Unknown"
                        res_title = res_song.get('title', '')
                        
                        score = match_score(db_art, db_tit, res_artists, res_title)
                        if score > s_best_score:
                            s_best_score = score
                            s_best_item = res
                            
                    if s_best_item and s_best_score >= 80:
                        formatted = format_date(s_best_item.get('radioDate'))
                        cache[song_db] = formatted
                        resolved_count += 1
                        resolved_any = True
                        print(f"    -> MATCH (Targeted): '{song_db}' -> {formatted} (Score: {s_best_score})")
                    else:
                        # Fallback al motore di ricerca web prima di contrassegnare come N/A
                        web_date = search_earone_via_web(song_db)
                        if web_date != "N/A":
                            cache[song_db] = web_date
                            resolved_count += 1
                            resolved_any = True
                            print(f"    -> MATCH (Web Fallback): '{song_db}' -> {web_date}")
                        else:
                            cache[song_db] = "N/A"
                            print(f"    -> NOT FOUND. Marking as N/A: '{song_db}'")
                else:
                    if c['year'] in ['2024', '2025', '2026'] or c['count'] >= 5:
                        # High priority missing, tenta la ricerca web prima di inserire N/A
                        web_date = search_earone_via_web(song_db)
                        if web_date != "N/A":
                            cache[song_db] = web_date
                            resolved_count += 1
                            resolved_any = True
                            print(f"    -> MATCH (Web Fallback): '{song_db}' -> {web_date}")
                        else:
                            cache[song_db] = "N/A"
                        
        if len(results) == 0:
            # Artist not found on EarOne at all
            for c in song_list:
                song_db = c['song']
                if c['year'] in ['2025', '2026']:
                    web_date = search_earone_via_web(song_db)
                    if web_date != "N/A":
                        cache[song_db] = web_date
                        resolved_count += 1
                        resolved_any = True
                        print(f"    -> MATCH (Web Fallback): '{song_db}' -> {web_date}")
                        continue
                cache[song_db] = "N/A"
                resolved_count += 1
                
        # Save cache every artist group
        save_json(cache, CACHE_FILE)
        time.sleep(1.5)
        
    save_json(cache, CACHE_FILE)
    print(f"\nDone! Resolved {resolved_count} songs. Total requests made: {requests_made}.")

if __name__ == "__main__":
    main()
