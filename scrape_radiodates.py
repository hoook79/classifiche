import json
import os
import re
import sys
import time
import urllib.parse
import subprocess
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

# --- CONFIGURATION ---
CACHE_FILE = 'song_radiodates_cache.json'
YEARS_CACHE_FILE = 'song_years_cache.json'

RTL_FILE = 'radio_rtl1025_history.json'
RDS_FILE = 'radio_rds_history.json'
ITALIA_FILE = 'radio_italia_history.json'

# --- PROMO & JINGLE FILTERING ---
_PROMO_PHONE = re.compile(r'\d{9,}'r'|\b\d{3}[\s\-./]\d{2}[\s\-./]\d{2}[\s\-./]\d{2,}'r'|\b\d{3}[\s\-./]\d{6,}', re.IGNORECASE)
_PROMO_URL = re.compile(r'https?://|www\.', re.IGNORECASE)
_PROMO_KW = re.compile(r'\bvocale\b|\bwhatsapp\b|\binvia\s+sms\b|\bmanda\s+(un|ora)\s|\bchiama\s+(il|ora|e)\s|\bsintonizzat|\bascoltaci\b|\bseguici\b|\bseguila\b|\bseguilo\b|\biscriviti\b|\babbonati\b|\bgiornale\s+radio\b|\btg\s+radio\b|\b(meteo|traffico|oroscopo)\b|\bnotiziario\b|\bspot\s+pub|\bjingle\b(?!\s+bells)|\bgingle\b|\bstacco\b|\bin\s+diretta\s+da\b|\bbuongiorno\s+da\b|\bbuona?\s+pomeriggio\s+da\b|\bbuona\s+serata\s+da\b|\bwebradio\b|\bpromo\b|\bident\b|\bsponsor\b|\bora\s+esatta\b|\bpubblicit[aà]\b', re.IGNORECASE)
_NEW_PROMO_PATTERNS = [re.compile(r'\bsu\s+radio\b', re.IGNORECASE), re.compile(r'\bdisco\s+novit[aà\']', re.IGNORECASE), re.compile(r'\bdj\s*set\b', re.IGNORECASE), re.compile(r'\bdance\s+time\b', re.IGNORECASE), re.compile(r'\bselezione\s+musicale\b', re.IGNORECASE), re.compile(r'\bsoft\s+club\b', re.IGNORECASE), re.compile(r'\bviabilit[aà\']\b', re.IGNORECASE), re.compile(r'\b3\s+minuti\s+alle\b', re.IGNORECASE), re.compile(r'\bcon\s+biba\b|\bsecci\s+biba\b|\bbiba\s+dee\s*j', re.IGNORECASE), re.compile(r'\bstramontignoso\b', re.IGNORECASE), re.compile(r'\bviniamo\b', re.IGNORECASE)]
_RADIO_NAME_EXACT = re.compile(r'^(radio\s+)?(subasio|divina|nostalgia|mitology|toscana|deejay|italia|rtl(\s*102\.5)?|rds|rai|105|m2o|virgin|r101|capital|freccia|gold|kiss\s*kiss|monte\s*carlo|studio\s*54|studio54|network|antenna)$', re.IGNORECASE)

def is_promo(song_str: str) -> bool:
    s = song_str.strip()
    if not s or len(s) < 4: return True
    if _PROMO_PHONE.search(s) or _PROMO_URL.search(s): return True
    if _PROMO_KW.search(s):
        if "oroscopo" in s.lower() and "calcutta" in s.lower(): pass
        else: return True
    for pattern in _NEW_PROMO_PATTERNS:
        if pattern.search(s): return True
    cleaned = re.sub(r'\s*\(\d{4}\)\s*$', '', s).strip()
    if ' - ' in cleaned:
        artist, title = cleaned.split(' - ', 1)
        if _RADIO_NAME_EXACT.match(artist.strip()) or artist.strip().lower() == 'promo' or title.strip().lower() == 'promo': return True
    else:
        if _RADIO_NAME_EXACT.match(cleaned): return True
    return False

def clean_song_name(s):
    s = s.strip()
    s = re.sub(r'^SRS\s+', '', s)
    s = re.sub(r'\s*\(\d{4}\)\s*$', '', s)
    return s.strip()

# --- ROBUST NORMALIZATION ---
def normalize_name(s):
    s = s.lower().strip()
    s = re.sub(r'\s*\(\d{4}\)\s*$', '', s)
    s = re.sub(r'\s*\(\d{4}\)', '', s)
    
    if ' - ' in s:
        parts = s.split(' - ', 1)
        artist_part = parts[0].strip()
        title_part = parts[1].strip()
    else:
        artist_part = ''
        title_part = s.strip()
        
    sep_pattern = r'\bfeat\.?\b|\bft\.?\b|\bfeaturing\b|&|\be\b|\band\b|,'
    artists = re.split(sep_pattern, artist_part)
    
    cleaned_artists = []
    for art in artists:
        art_clean = re.sub(r'[^a-z0-9]', '', art)
        if art_clean:
            cleaned_artists.append(art_clean)
            
    cleaned_artists.sort()
    canonical_artist = "".join(cleaned_artists)
    canonical_title = re.sub(r'[^a-z0-9]', '', title_part)
    
    if canonical_artist:
        return f"{canonical_artist}|{canonical_title}"
    else:
        return canonical_title

# --- LOADER & SAVER ---
def load_json(path, default):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except Exception as e:
                print(f"Error loading {path}: {e}")
                return default
    return default

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# --- SCRAPER LOGIC ---
def search_earone(query):
    encoded_query = urllib.parse.quote(query)
    url = f"https://www.earone.it/radio-date/all?search={encoded_query}"
    
    result = subprocess.run(
        ["curl.exe", "-s", "-L", "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", url],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore'
    )
    
    html = result.stdout
    soup = BeautifulSoup(html, 'html.parser')
    
    large_script = None
    for s in soup.find_all('script'):
        text = s.string or ''
        if len(text) > 1000 and 'pageProps' in text:
            large_script = text
            break
            
    if large_script:
        start_idx = large_script.find('{')
        end_idx = large_script.rfind('}')
        if start_idx != -1 and end_idx != -1:
            try:
                data = json.loads(large_script[start_idx:end_idx+1])
                page_props = data.get('props', {}).get('pageProps', data.get('pageProps', {}))
                return page_props.get('filteredRadioDate', [])
            except Exception as e:
                pass
    return []

def main():
    # Load caches
    years_cache = load_json(YEARS_CACHE_FILE, {})
    radiodates_cache = load_json(CACHE_FILE, {})
    
    # Normalise current cache for checking
    normalized_cache = {normalize_name(k): v for k, v in radiodates_cache.items()}
    
    # 1. Collect all songs from history files
    print("Collecting songs from playlists...")
    all_radios = [
        ('rtl', RTL_FILE),
        ('rds', RDS_FILE),
        ('italia', ITALIA_FILE),
        ('subasio', 'radio_subasio_history.json'),
        ('divina', 'radio_divina_history.json'),
        ('mitology', 'radio_mitology_history.json'),
        ('nostalgia', 'radio_nostalgia_history.json'),
        ('toscana', 'radio_toscana_history.json')
    ]
    
    radio_songs = {r: set() for r, _ in all_radios}
    all_unique_songs = set()
    
    for r, filepath in all_radios:
        if os.path.exists(filepath):
            data = load_json(filepath, [])
            for item in data:
                s = clean_song_name(item['song'])
                if not is_promo(s):
                    radio_songs[r].add(s)
                    all_unique_songs.add(s)
                    
    print(f"Total unique songs across all files: {len(all_unique_songs)}")
    
    # 2. Identify pre-2010 songs and resolve them to 'N/D' directly
    pre_2010_count = 0
    to_scrape = []
    
    for song in sorted(all_unique_songs):
        norm_key = normalize_name(song)
        if norm_key in normalized_cache:
            continue # Already in cache
            
        # Check publication year
        year = years_cache.get(song)
        if year and year != 'N/A':
            try:
                yr_val = int(year)
                if yr_val < 2010:
                    radiodates_cache[song] = 'N/D'
                    normalized_cache[norm_key] = 'N/D'
                    pre_2010_count += 1
                    continue
            except:
                pass
        to_scrape.append(song)
        
    print(f"Automatically marked {pre_2010_count} older songs as 'N/D'.")
    print(f"Total unique songs needing active scraping: {len(to_scrape)}")
    
    if pre_2010_count > 0:
        save_json(CACHE_FILE, radiodates_cache)
        print("Incremental cache saved.")
        
    if not to_scrape:
        print("Nothing to scrape. Everything is resolved!")
        return
        
    # 3. Sort to-scrape list to prioritize RTL 102.5, RDS, and Radio Italia
    def get_priority(song):
        # Return 0 for RTL, 1 for Italia, 2 for RDS, 3 for others
        if song in radio_songs['rtl']:
            return 0
        if song in radio_songs['italia']:
            return 1
        if song in radio_songs['rds']:
            return 2
        return 3
        
    to_scrape.sort(key=lambda s: (get_priority(s), s.lower()))
    
    # Let's count priority distributions
    p_counts = {0: 0, 1: 0, 2: 0, 3: 0}
    for s in to_scrape:
        p_counts[get_priority(s)] += 1
        
    print(f"Scraping queue priority:")
    print(f"  - RTL 102.5 songs: {p_counts[0]}")
    print(f"  - Radio Italia songs: {p_counts[1]}")
    print(f"  - RDS songs: {p_counts[2]}")
    print(f"  - Other radio songs: {p_counts[3]}")
    
    print("\nStarting scraping process...")
    resolved = 0
    not_found = 0
    
    for i, song in enumerate(to_scrape):
        norm_key = normalize_name(song)
        if norm_key in normalized_cache:
            continue # Might have been populated in a batch match
            
        print(f"[{i+1}/{len(to_scrape)}] Scraping: '{song}'")
        
        # Decide query. If format is 'Artist - Title', we search by title
        title_query = song
        if ' - ' in song:
            parts = song.split(' - ', 1)
            title_query = parts[1].strip() # Search by title to be robust
            
        # If title is too short, search by full name
        if len(title_query) < 3:
            title_query = song
            
        results = search_earone(title_query)
        
        # Process results
        matched = False
        if results:
            for item in results:
                # Get details of search result
                res_title = item.get('song', {}).get('title', '')
                res_artists = []
                if item.get('song', {}).get('tracks'):
                    for t in item['song']['tracks']:
                        for a in t.get('artists', []):
                            res_artists.append(a.get('name', ''))
                
                # Combine
                res_artist_str = ", ".join(res_artists)
                res_full_name = f"{res_artist_str} - {res_title}"
                res_norm = normalize_name(res_full_name)
                
                # Format date YYYY-MM-DD -> DD/MM/YYYY
                raw_date = item.get('radioDate', '')
                formatted_date = 'N/D'
                if raw_date and len(raw_date) == 10:
                    pts = raw_date.split('-')
                    if len(pts) == 3:
                        formatted_date = f"{pts[2]}/{pts[1]}/{pts[0]}"
                
                # Add to cache!
                # Store it under the search result's name
                radiodates_cache[res_full_name] = formatted_date
                normalized_cache[res_norm] = formatted_date
                
                # Check if this match corresponds to our searched song
                if res_norm == norm_key:
                    matched = True
                    print(f"  -> Exact Match: '{res_full_name}' -> {formatted_date}")
                    resolved += 1
                    
            if not matched:
                # See if there is a fuzzy match or if we can find it in the results
                # Let's check if any result normalized matches our key
                # (sometimes spacing/separators are slightly different)
                for item in results:
                    res_title = item.get('song', {}).get('title', '')
                    res_artists = [a.get('name', '') for t in item.get('song', {}).get('tracks', []) for a in t.get('artists', [])]
                    # Check if our title is in the result title and our primary artist is in result artists
                    if ' - ' in song:
                        art_part = song.split(' - ', 1)[0].lower()
                        title_part = song.split(' - ', 1)[1].lower()
                        # Clean them
                        art_clean = re.sub(r'[^a-z0-9]', '', art_part)
                        title_clean = re.sub(r'[^a-z0-9]', '', title_part)
                        
                        res_title_clean = re.sub(r'[^a-z0-9]', '', res_title.lower())
                        res_artists_clean = "".join([re.sub(r'[^a-z0-9]', '', a.lower()) for a in res_artists])
                        
                        if title_clean == res_title_clean or title_clean in res_title_clean or res_title_clean in title_clean:
                            # Check if at least one artist name overlaps
                            overlap = False
                            for a in res_artists:
                                a_clean = re.sub(r'[^a-z0-9]', '', a.lower())
                                if a_clean in art_clean or art_clean in a_clean:
                                    overlap = True
                                    break
                            if overlap:
                                raw_date = item.get('radioDate', '')
                                formatted_date = 'N/D'
                                if raw_date and len(raw_date) == 10:
                                    pts = raw_date.split('-')
                                    formatted_date = f"{pts[2]}/{pts[1]}/{pts[0]}"
                                radiodates_cache[song] = formatted_date
                                normalized_cache[norm_key] = formatted_date
                                matched = True
                                print(f"  -> Fuzzy Match: '{song}' matched with '{res_title}' -> {formatted_date}")
                                resolved += 1
                                break
                                
        if not matched:
            # If not found, write as 'N/D' so we don't query again
            radiodates_cache[song] = 'N/D'
            normalized_cache[norm_key] = 'N/D'
            print(f"  -> Not Found. Marked as N/D.")
            not_found += 1
            
        # Save cache incrementally
        save_json(CACHE_FILE, radiodates_cache)
        
        # Sleep to avoid rate limiting
        time.sleep(1.2)

    print("\nScraping complete!")
    print(f"Resolved: {resolved} songs.")
    print(f"Not found: {not_found} songs.")

if __name__ == "__main__":
    main()
