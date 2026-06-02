#!/usr/bin/env python3
"""
genera_html.py
Genera classifica_radio.html leggendo i file JSON di storia delle trasmissioni.
Days contiene array di orari per ogni data, usato per popup al click sui passaggi.
"""
import json
import os
import re
import unicodedata
from collections import defaultdict, Counter
from datetime import datetime

# Inserisci l'URL dell'applicazione web fornito da Google Apps Script dopo il deployment
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbx_p44hQCjBjPvNOdM5whPI3hgd8SA96gbAcwva3ywe8CRjci4RAYUQXYc4oVMuzEic/exec"

# ── Percorsi ───────────────────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.abspath(__file__))
SUBASIO_JSON   = os.path.join(BASE, 'radio_subasio_history.json')
DIVINA_JSON    = os.path.join(BASE, 'radio_divina_history.json')
MITOLOGY_JSON  = os.path.join(BASE, 'radio_mitology_history.json')
NOSTALGIA_JSON = os.path.join(BASE, 'radio_nostalgia_history.json')
TOSCANA_JSON   = os.path.join(BASE, 'radio_toscana_history.json')
ITALIA_JSON    = os.path.join(BASE, 'radio_italia_history.json')
RDS_JSON       = os.path.join(BASE, 'radio_rds_history.json')
RTL1025_JSON   = os.path.join(BASE, 'radio_rtl1025_history.json')
CACHE_YEARS    = os.path.join(BASE, 'song_years_cache.json')
CACHE_OVERRIDES = os.path.join(BASE, 'manual_years_override.json')
CACHE_RADIODATES = os.path.join(BASE, 'song_radiodates_cache.json')
CACHE_RADIODATES_OVERRIDES = os.path.join(BASE, 'manual_radiodates_override.json')
CACHE_PREVIEWS = os.path.join(BASE, 'preview_cache.json')
OUT_HTML       = os.path.join(BASE, 'classifica_radio.html')

# ── Helpers ────────────────────────────────────────────────────────────────────
def parse_subasio_song(s):
    """Ritorna (artist, title) da 'ARTIST - TITLE'"""
    s = re.sub(r'^SRS\s+', '', s).strip()
    if ' - ' in s:
        artist, title = s.split(' - ', 1)
        return artist.strip(), title.strip()
    return s.strip(), ''

def parse_divina_song(s):
    """Ritorna (artist, title, year) da 'ARTIST - TITLE (YEAR)'"""
    year_match = re.search(r'\((\d{4})\)\s*$', s)
    year = year_match.group(1) if year_match else 'N/A'
    cleaned = re.sub(r'\s*\(\d{4}\)\s*$', '', s).strip()
    if ' - ' in cleaned:
        artist, title = cleaned.split(' - ', 1)
        return artist.strip().title(), title.strip().title(), year
    return cleaned.strip().title(), '', year

def normalize_name(s):
    """
    Super-robust normalization of a song name (format 'Artist - Title' or just 'Title').
    - Lowers the string.
    - Normalizes accented characters to ASCII.
    - Strips years in parentheses like (2026).
    - Splits by ' - ' into artist and title.
    - Standardizes featured artist tags, conjunctions, and delimiters.
    - Merges featured artists from title to artist list if not already present.
    - Cleans version/remix suffixes from title and parentheticals.
    - Alphabetically sorts words within each artist's name.
    - Deduplicates and sorts multiple artists alphabetically so order doesn't matter.
    - Returns a canonical key.
    """
    # Replace common replacement characters or broken unicode accents
    s = s.replace('\ufffd', 'e')
    # Convert accented characters to ASCII (e.g. è -> e)
    s = unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('ASCII')
    s = s.lower().strip()
    # Strip year in parentheses
    s = re.sub(r'\s*\(\d{4}\)\s*$', '', s)
    s = re.sub(r'\s*\(\d{4}\)', '', s)
    
    if ' - ' in s:
        parts = s.split(' - ', 1)
        artist_part = parts[0].strip()
        title_part = parts[1].strip()
    else:
        artist_part = ''
        title_part = s.strip()
        
    # Standardize MC spacing (e.g. "Mc Cartney" -> "McCartney")
    artist_part = re.sub(r'\bmc\s+', 'mc', artist_part, flags=re.I)
    # Standardize All Stars spacing
    artist_part = re.sub(r'\ball\s*stars?\b', 'allstars', artist_part, flags=re.I)
    # Strip dots to handle acronyms (e.g. R.E.O. -> REO, U.B.40 -> UB40) before splitting
    artist_part = artist_part.replace('.', '')
    
    # Extract featured artists from title part if present
    title_clean = title_part
    feat_pattern = r'\b(feat|ft|featuring|with)\b\.?\s*(.*?)(?:\)|$)'
    feat_match = re.search(feat_pattern, title_part, flags=re.I)
    if feat_match:
        add_art = feat_match.group(2).lower()
        art_part_clean = re.sub(r'[^a-z0-9]', '', artist_part.lower())
        add_art_clean = re.sub(r'[^a-z0-9]', '', add_art)
        if add_art_clean and add_art_clean not in art_part_clean:
            artist_part += " , " + feat_match.group(2)
        title_clean = re.sub(feat_pattern, '', title_part, flags=re.I)
        
    # Strip parentheticals that contain version/remix keywords
    version_kw = r'\b(radio|edit|version|remix|rmx|mix|live|acoustic|instrumental|extended|single|album|cover|tribute|original|mono|stereo|remastered|remaster)\b'
    title_clean = re.sub(r'\(\s*.*?' + version_kw + r'.*?\)', '', title_clean, flags=re.I)
    
    # Strip separators followed by version keywords at the end of the title
    title_clean = re.sub(r'\s*[\-–—,/]\s*.*?' + version_kw + r'.*?$', '', title_clean, flags=re.I)
    
    # Strip any remaining parentheses characters but keep their contents
    title_clean = title_clean.replace('(', ' ').replace(')', ' ')
    title_clean = re.sub(r'\s+', ' ', title_clean).strip()
    
    # Normalize artist part
    sep_pattern = r'\bfeat\.?\b|\bft\.?\b|\bfeaturing\b|&|\be\b|\band\b|,|/|\+'
    artists = re.split(sep_pattern, artist_part)
    
    cleaned_artists = []
    for art in artists:
        # Remove dots first to handle acronyms (e.g. R.E.O. -> REO, U.B.40 -> UB40)
        art_clean = art.replace('.', '')
        # Split individual artist by spaces and sort their words alphabetically
        words = re.split(r'[\s\-_]+', art_clean)
        cleaned_words = []
        for w in words:
            w_clean = re.sub(r'[^a-z0-9]', '', w.lower())
            if w_clean and w_clean not in ['the', 'band', 'group']:
                cleaned_words.append(w_clean)
        cleaned_words.sort()
        art_clean = "".join(cleaned_words)
        if art_clean and art_clean not in cleaned_artists:
            cleaned_artists.append(art_clean)
            
    # Sort artists alphabetically
    cleaned_artists.sort()
    canonical_artist = "".join(cleaned_artists)
    
    # Normalize title part: strip non-alphanumeric
    canonical_title = re.sub(r'[^a-z0-9]', '', title_clean)
    
    if canonical_artist:
        return f"{canonical_artist}|{canonical_title}"
    else:
        return canonical_title


# ── Filtro jingle/promo ────────────────────────────────────────────────────────
# Pattern sicuri: numeri di telefono, URL, hashtag
_PROMO_PHONE = re.compile(
    r'\d{9,}'                                    # numero lungo senza spazi
    r'|\b\d{3}[\s\-./]\d{2}[\s\-./]\d{2}[\s\-./]\d{2,}'  # 338 63 60 114
    r'|\b\d{3}[\s\-./]\d{6,}',                  # 338 636011...
    re.IGNORECASE
)
_PROMO_URL = re.compile(r'https?://|www\.', re.IGNORECASE)

# Frasi e parole chiave con word boundary per evitare falsi positivi
# (es. "meteo" NON deve matchare "meteor", "traffico" NON deve matchare "trafficker")
_PROMO_KW = re.compile(
    r'\bvocale\b'                       # "manda un vocale"
    r'|\bwhatsapp\b'
    r'|\binvia\s+sms\b'
    r'|\bmanda\s+(un|ora)\s'            # "manda un messaggio", "manda ora"
    r'|\bchiama\s+(il|ora|e)\s'         # "chiama il 338", "chiama ora"
    r'|\bsintonizzat'                   # "sintonizzati"
    r'|\bascoltaci\b'
    r'|\bseguici\b|\bseguila\b|\bseguilo\b'
    r'|\biscriviti\b|\babbonati\b'
    r'|\bgiornale\s+radio\b'
    r'|\btg\s+radio\b'
    r'|\b(meteo|traffico|oroscopo)\b'   # solo parola intera
    r'|\bnotiziario\b'
    r'|\bspot\s+pub'                    # "spot pubblicitario"
    r'|\bjingle\b(?!\s+bells)|\bgingle\b'  # jingle radio, ma NON "Jingle Bells"
    r'|\bstacco\b'
    r'|\bin\s+diretta\s+da\b'
    r'|\bbuongiorno\s+da\b'
    r'|\bbuona?\s+pomeriggio\s+da\b'
    r'|\bbuona\s+serata\s+da\b'
    r'|\bwebradio\b'                    # "WEBRADIO"
    r'|\bpromo\b'                       # "PROMO"
    r'|\bident\b'                       # stacchetto identificativo
    r'|\bsponsor\b'
    r'|\bora\s+esatta\b'
    r'|\bpubblicit[aà]\b',             # "pubblicità"
    re.IGNORECASE
)

# Nuovi pattern aggiuntivi per programmi, jingle e annunci radio
_NEW_PROMO_PATTERNS = [
    re.compile(r'\bsu\s+radio\b', re.IGNORECASE),              # "su radio"
    re.compile(r'\bdisco\s+novit[aà\']', re.IGNORECASE),       # "disco novita/novità/novita'"
    re.compile(r'\bdj\s*set\b', re.IGNORECASE),                 # "dj set", "dj-set"
    re.compile(r'\bdance\s+time\b', re.IGNORECASE),             # "dance time"
    re.compile(r'\bselezione\s+musicale\b', re.IGNORECASE),     # "selezione musicale"
    re.compile(r'\bsoft\s+club\b', re.IGNORECASE),              # "soft club"
    re.compile(r'\bviabilit[aà\']\b', re.IGNORECASE),           # "viabilità", "viabilita'"
    re.compile(r'\b3\s+minuti\s+alle\b', re.IGNORECASE),        # "3 minuti alle 4:00"
    re.compile(r'\bcon\s+biba\b|\bsecci\s+biba\b|\bbiba\s+dee\s*j', re.IGNORECASE), # Biba / Andrea Secci jingles
    re.compile(r'\bstramontignoso\b', re.IGNORECASE),           # Stramontignoso promo/show
    re.compile(r'\bviniamo\b', re.IGNORECASE),                  # Viniamo promo/show
]

# Nome di radio esatto (con ancoraggio completo per evitare falsi positivi come "Capital Cities")
_RADIO_NAME_EXACT = re.compile(
    r'^(radio\s+)?(subasio|divina|nostalgia|mitology|toscana|deejay|italia|'
    r'rtl(\s*102\.5)?|rds|rai|105|m2o|virgin|r101|capital|freccia|gold|'
    r'kiss\s*kiss|monte\s*carlo|studio\s*54|studio54|network|antenna)$',
    re.IGNORECASE
)

def is_promo(song_str: str) -> bool:
    """
    Ritorna True se la stringa sembra un jingle, promo o annuncio,
    non una canzone vera e propria.
    """
    s = song_str.strip()
    if not s or len(s) < 4:
        return True

    # Numero di telefono o URL → certamente promo
    if _PROMO_PHONE.search(s) or _PROMO_URL.search(s):
        return True

    # Parole chiave promo originali
    if _PROMO_KW.search(s):
        # Eccezione per la canzone reale "Oroscopo" di Calcutta
        if "oroscopo" in s.lower() and "calcutta" in s.lower():
            pass
        else:
            return True

    # Nuovi pattern aggiuntivi per programmi, jingle e annunci radio
    for pattern in _NEW_PROMO_PATTERNS:
        if pattern.search(s):
            return True

    # Controllo sul nome della radio (come artista o stringa singola)
    cleaned = re.sub(r'\s*\(\d{4}\)\s*$', '', s).strip()
    if ' - ' in cleaned:
        artist, title = cleaned.split(' - ', 1)
        artist_clean = artist.strip()
        title_clean = title.strip()
        
        # Se l'artista è esattamente il nome di una radio, è un jingle/promo
        if _RADIO_NAME_EXACT.match(artist_clean):
            return True
        # Se una delle parti è solo "promo"
        if artist_clean.lower() == 'promo' or title_clean.lower() == 'promo':
            return True
    else:
        # Stringa senza trattino che è esattamente il nome di una radio
        if _RADIO_NAME_EXACT.match(cleaned):
            return True

    return False

def sort_date_key(d):
    """Sort key per date DD.MM (assumiamo anno corrente, gestisce cambio anno)"""
    try:
        parts = d.split('.')
        day, month = int(parts[0]), int(parts[1])
        # Assume anno 2025-2026: mesi >= 10 sono 2025, mesi <= 9 sono 2026
        year = 2025 if month >= 10 else 2026
        return datetime(year, month, day)
    except:
        return datetime(2026, 1, 1)

def levenshtein_distance(s1, s2):
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
        
    return previous_row[-1]

def check_artists_overlap(words1, words2):
    w1 = set(words1)
    w2 = set(words2)
    w1.discard('')
    w2.discard('')
    if not w1 or not w2:
        return False
    # If one is a subset of another, they match!
    if w1.issubset(w2) or w2.issubset(w1):
        return True
    # Or if they share at least 2 significant words (length >= 3)
    sig_intersection = {w for w in w1.intersection(w2) if len(w) >= 3}
    if len(sig_intersection) >= 2:
        return True
    return False

def build_global_canonical_mapping(song_counts, years_cache, overrides):
    """
    Raggruppa tutti i brani in chiavi canoniche univoche unendo i doppioni
    (stesso titolo normalizzato e artisti simili/sovrapposti).
    """
    title_groups = defaultdict(list)
    song_info = {}
    
    for raw_name in song_counts:
        # Convert raw name for accent check or special character normalization
        raw_normalized = raw_name.replace('\ufffd', 'e')
        raw_normalized = unicodedata.normalize('NFKD', raw_normalized).encode('ASCII', 'ignore').decode('ASCII')
        
        cleaned = re.sub(r'\s*\(\d{4}\)\s*$', '', raw_normalized).strip()
        if ' - ' in cleaned:
            artist, title = cleaned.split(' - ', 1)
            artist = artist.strip()
            title = title.strip()
        else:
            artist, title = '', cleaned
            
        title_clean = title
        feat_pattern = r'\b(feat|ft|featuring|with)\b\.?\s*(.*?)(?:\)|$)'
        feat_match = re.search(feat_pattern, title, flags=re.I)
        if feat_match:
            add_art = feat_match.group(2)
            title_clean = re.sub(feat_pattern, '', title, flags=re.I)
            norm_artist_part = artist + " , " + add_art
        else:
            norm_artist_part = artist
            
        # Get canonical key to extract the robust normalized title
        canonical_key = normalize_name(raw_name)
        norm_title = canonical_key.split('|')[1] if '|' in canonical_key else canonical_key
        
        # Standardize MC spacing and All Stars spacing in artist part for word extraction
        norm_artist_part = re.sub(r'\bmc\s+', 'mc', norm_artist_part, flags=re.I)
        norm_artist_part = re.sub(r'\ball\s*stars?\b', 'allstars', norm_artist_part, flags=re.I)
        # Strip dots to handle acronyms (e.g. R.E.O. -> REO, U.B.40 -> UB40) before splitting
        norm_artist_part = norm_artist_part.replace('.', '')
        
        # Normalizza la parte artista
        sep_pattern = r'\bfeat\.?\b|\bft\.?\b|\bfeaturing\b|&|\be\b|\band\b|,|/|\+'
        parts = re.split(sep_pattern, norm_artist_part.lower())
        
        cleaned_artists = []
        artist_words = []
        for p in parts:
            # Remove dots first to handle acronyms (e.g. R.E.O. -> REO, U.B.40 -> UB40)
            p_clean = p.strip().replace('.', '')
            # Split individual artist by spaces and sort their words alphabetically
            words = re.split(r'[\s\-_]+', p_clean)
            cleaned_words = []
            for w in words:
                w_clean = re.sub(r'[^a-z0-9]', '', w.lower())
                if w_clean and w_clean not in ['the', 'band', 'group', 'and', 'e', 'with']:
                    cleaned_words.append(w_clean)
                    if w_clean not in artist_words:
                        artist_words.append(w_clean)
            cleaned_words.sort()
            art_clean = "".join(cleaned_words)
            if art_clean and art_clean not in cleaned_artists:
                cleaned_artists.append(art_clean)
        cleaned_artists.sort()
        
        # Keep original raw artist and title for canonical_to_spelling spelling mapping
        orig_cleaned = re.sub(r'\s*\(\d{4}\)\s*$', '', raw_name).strip()
        if ' - ' in orig_cleaned:
            orig_artist, orig_title = orig_cleaned.split(' - ', 1)
            orig_artist, orig_title = orig_artist.strip(), orig_title.strip()
        else:
            orig_artist, orig_title = '', orig_cleaned
            
        song_info[raw_name] = {
            'artist': orig_artist,
            'title': orig_title,
            'norm_title': norm_title,
            'artists_list': cleaned_artists,
            'artist_words': artist_words,
            'clean_artist_str': "".join(cleaned_artists)
        }
        
        if norm_title:
            title_groups[norm_title].append(raw_name)
            
    raw_to_canonical = {}
    canonical_to_spelling = {}
    
    for norm_title, raw_list in title_groups.items():
        clusters = []
        # Ordina per frequenza decrescente in modo che la grafia più comune diventi il leader
        raw_list_sorted = sorted(raw_list, key=lambda x: song_counts[x], reverse=True)
        
        for raw_name in raw_list_sorted:
            info = song_info[raw_name]
            matched_cluster_idx = -1
            for idx, cluster in enumerate(clusters):
                # Confronta con tutti i membri del cluster per supportare catene a maglia singola (single-linkage)
                matched = False
                for member_name in cluster:
                    member_info = song_info[member_name]
                    overlap = check_artists_overlap(info['artist_words'], member_info['artist_words'])
                    similar = False
                    if not overlap:
                        dist = levenshtein_distance(info['clean_artist_str'], member_info['clean_artist_str'])
                        max_len = max(len(info['clean_artist_str']), len(member_info['clean_artist_str']))
                        if max_len > 0 and (dist <= 2 or (dist / max_len) <= 0.15):
                            similar = True
                    if overlap or similar:
                        matched = True
                        break
                if matched:
                    matched_cluster_idx = idx
                    break
                    
            if matched_cluster_idx != -1:
                clusters[matched_cluster_idx].append(raw_name)
            else:
                clusters.append([raw_name])
                
        for cluster in clusters:
            rep_name = cluster[0]
            canonical_key = normalize_name(rep_name)
            rep_info = song_info[rep_name]
            canonical_to_spelling[canonical_key] = (rep_info['artist'], rep_info['title'])
            for raw_name in cluster:
                raw_to_canonical[raw_name] = canonical_key
                
    return raw_to_canonical, canonical_to_spelling

# Tenta di sincronizzare gli override da Google Sheets prima di caricare i dati
try:
    from google_sheets_sync import download_overrides
    download_overrides()
except Exception as e:
    print(f"  [GOOGLE SHEETS] Impossibile scaricare gli override: {e}")

# ── Carica dati ───────────────────────────────────────────────────────────────
print("Caricamento dati...")

with open(SUBASIO_JSON, 'r', encoding='utf-8') as f:
    subasio_history = json.load(f)

with open(DIVINA_JSON, 'r', encoding='utf-8') as f:
    divina_history = json.load(f)

mitology_history = []
if os.path.exists(MITOLOGY_JSON):
    with open(MITOLOGY_JSON, 'r', encoding='utf-8') as f:
        mitology_history = json.load(f)

nostalgia_history = []
if os.path.exists(NOSTALGIA_JSON):
    with open(NOSTALGIA_JSON, 'r', encoding='utf-8') as f:
        nostalgia_history = json.load(f)

toscana_history = []
if os.path.exists(TOSCANA_JSON):
    with open(TOSCANA_JSON, 'r', encoding='utf-8') as f:
        toscana_history = json.load(f)

italia_history = []
if os.path.exists(ITALIA_JSON):
    with open(ITALIA_JSON, 'r', encoding='utf-8') as f:
        italia_history = json.load(f)

rds_history = []
if os.path.exists(RDS_JSON):
    with open(RDS_JSON, 'r', encoding='utf-8') as f:
        rds_history = json.load(f)

rtl1025_history = []
if os.path.exists(RTL1025_JSON):
    with open(RTL1025_JSON, 'r', encoding='utf-8') as f:
        rtl1025_history = json.load(f)

years_cache = {}
if os.path.exists(CACHE_YEARS):
    with open(CACHE_YEARS, 'r', encoding='utf-8') as f:
        years_cache = json.load(f)

# Applica gli override manuali sopra la cache
if os.path.exists(CACHE_OVERRIDES):
    with open(CACHE_OVERRIDES, 'r', encoding='utf-8') as f:
        try:
            overrides = json.load(f)
            years_cache.update(overrides)
            print(f"  Override manuali applicati: {len(overrides)} brani aggiornati.")
        except Exception as e:
            print(f"  Errore nel caricamento degli override: {e}")

# Cache normalizzata per lookup robusto case/punctuation-insensitive
normalized_years_cache = {normalize_name(k): v for k, v in years_cache.items() if v != 'N/A'}

radiodates_cache = {}
if os.path.exists(CACHE_RADIODATES):
    with open(CACHE_RADIODATES, 'r', encoding='utf-8') as f:
        try:
            radiodates_cache = json.load(f)
        except Exception as e:
            print(f"  Errore nel caricamento della cache delle radio date: {e}")

if os.path.exists(CACHE_RADIODATES_OVERRIDES):
    with open(CACHE_RADIODATES_OVERRIDES, 'r', encoding='utf-8') as f:
        try:
            radiodates_overrides = json.load(f)
            radiodates_cache.update(radiodates_overrides)
            print(f"  Override manuali radio date applicati: {len(radiodates_overrides)} brani aggiornati.")
        except Exception as e:
            print(f"  Errore nel caricamento degli override delle radio date: {e}")

# Cache normalizzata per lookup robusto
normalized_radiodates_cache = {normalize_name(k): v for k, v in radiodates_cache.items() if v != 'N/A' and v != 'N/D'}

# Costruzione mappatura canonica globale per unire i doppioni
print("Costruzione mappatura canonica globale per rimuovere doppioni...")
global_song_counts = Counter()
for history in [subasio_history, divina_history, mitology_history, nostalgia_history, toscana_history, italia_history, rds_history, rtl1025_history]:
    for item in history:
        global_song_counts[item['song']] += 1

raw_to_canonical, canonical_to_spelling = build_global_canonical_mapping(global_song_counts, years_cache, overrides)
print(f"  Mappatura completata: {len(raw_to_canonical)} grafie unite in {len(canonical_to_spelling)} canzoni canoniche.")

preview_cache = {}
if os.path.exists(CACHE_PREVIEWS):
    with open(CACHE_PREVIEWS, 'r', encoding='utf-8') as f:
        preview_cache = json.load(f)
    n_preview = sum(1 for v in preview_cache.values() if v)
    print(f"  Preview cache: {len(preview_cache)} brani ({n_preview} con URL)")

# ── Processa Radio Subasio ────────────────────────────────────────────────────
print("Elaborazione Radio Subasio...")

# song_stats[norm_key] = {artist, title, year, radioDate, total, days: {date: [time, ...]}}
subasio_stats = defaultdict(lambda: {
    'artist': '', 'title': '', 'year': 'N/A', 'radioDate': 'N/A', 'total': 0,
    'days': defaultdict(list)
})
subasio_dates = set()

for item in subasio_history:
    raw_name = re.sub(r'^SRS\s+', '', item['song']).strip()
    if is_promo(raw_name):
        continue
    artist, title = parse_subasio_song(item['song'])
    date = item['date']
    time = item['time']

    norm_key = raw_to_canonical.get(item['song'], normalize_name(raw_name))
    best_artist, best_title = canonical_to_spelling.get(norm_key, (artist, title))

    # Cerca anno nella cache normalizzata
    year = normalized_years_cache.get(norm_key, 'N/A')
    # Anche da titolo: "(2003)" nel nome
    m = re.search(r'\((\d{4})\)', raw_name)
    if m:
        year = m.group(1)

    radio_date = normalized_radiodates_cache.get(norm_key, 'N/A')

    s = subasio_stats[norm_key]
    s['artist'] = best_artist
    s['title'] = best_title
    if s['year'] == 'N/A' and year != 'N/A':
        s['year'] = year
    if s.get('radioDate', 'N/A') == 'N/A' and radio_date != 'N/A':
        s['radioDate'] = radio_date
    s['total'] += 1
    s['days'][date].append(time)
    subasio_dates.add(date)

# Ordina date decrescente (più recente prima)
subasio_dates_sorted = sorted(subasio_dates, key=sort_date_key, reverse=True)

# Prepara lista ordinata per totale
subasio_ranked = sorted(subasio_stats.values(), key=lambda x: x['total'], reverse=True)
for i, s in enumerate(subasio_ranked):
    s['rank'] = i + 1
    s['days'] = dict(s['days'])  # converti defaultdict in dict

print(f"  Subasio: {len(subasio_ranked)} brani, {len(subasio_dates_sorted)} giorni")

# ── Processa Radio Divina ─────────────────────────────────────────────────────
print("Elaborazione Radio Divina...")

divina_stats = defaultdict(lambda: {
    'artist': '', 'title': '', 'year': 'N/A', 'radioDate': 'N/A', 'total': 0,
    'days': defaultdict(list)
})
divina_dates = set()

for item in divina_history:
    if is_promo(item['song']):
        continue
    artist, title, year = parse_divina_song(item['song'])
    raw_name = f"{artist} - {title}"
    
    norm_key = raw_to_canonical.get(item['song'], normalize_name(raw_name))
    best_artist, best_title = canonical_to_spelling.get(norm_key, (artist, title))
    
    if year == 'N/A':
        year = normalized_years_cache.get(norm_key, 'N/A')
    radio_date = normalized_radiodates_cache.get(norm_key, 'N/A')
    date = item['date']
    time = item['time']

    s = divina_stats[norm_key]
    s['artist'] = best_artist
    s['title'] = best_title
    if s['year'] == 'N/A' and year != 'N/A':
        s['year'] = year
    if s.get('radioDate', 'N/A') == 'N/A' and radio_date != 'N/A':
        s['radioDate'] = radio_date
    s['total'] += 1
    s['days'][date].append(time)
    divina_dates.add(date)

divina_dates_sorted = sorted(divina_dates, key=sort_date_key, reverse=True)

divina_ranked = sorted(divina_stats.values(), key=lambda x: x['total'], reverse=True)
for i, s in enumerate(divina_ranked):
    s['rank'] = i + 1
    s['days'] = dict(s['days'])

print(f"  Divina: {len(divina_ranked)} brani, {len(divina_dates_sorted)} giorni")

# ── Processa radio generica (Mitology / Nostalgia) ────────────────────────────
def process_generic_radio(history, label):
    stats = defaultdict(lambda: {
        'artist': '', 'title': '', 'year': 'N/A', 'radioDate': 'N/A', 'total': 0,
        'days': defaultdict(list)
    })
    dates = set()
    
    for item in history:
        raw = item['song'].strip()
        if is_promo(raw):
            continue
        year_m = re.search(r'\((\d{4})\)\s*$', raw)
        year = year_m.group(1) if year_m else 'N/A'
        cleaned = re.sub(r'\s*\(\d{4}\)\s*$', '', raw).strip()
        
        norm_key = raw_to_canonical.get(item['song'], normalize_name(cleaned))
        
        if ' - ' in cleaned:
            artist, title = cleaned.split(' - ', 1)
            artist = artist.strip().title()
            title  = title.strip().title()
        else:
            artist, title = cleaned.title(), ''
            
        best_artist, best_title = canonical_to_spelling.get(norm_key, (artist, title))
        
        if year == 'N/A':
            year = normalized_years_cache.get(norm_key, 'N/A')
        radio_date = normalized_radiodates_cache.get(norm_key, 'N/A')
        
        s = stats[norm_key]
        s['artist'] = best_artist
        s['title'] = best_title
        if s['year'] == 'N/A' and year != 'N/A':
            s['year'] = year
        if s.get('radioDate', 'N/A') == 'N/A' and radio_date != 'N/A':
            s['radioDate'] = radio_date
        s['total'] += 1
        s['days'][item['date']].append(item['time'])
        dates.add(item['date'])
            
    dates_sorted = sorted(dates, key=sort_date_key, reverse=True)
    ranked = sorted(stats.values(), key=lambda x: x['total'], reverse=True)
    for i, s in enumerate(ranked):
        s['rank'] = i + 1
        s['days'] = dict(s['days'])
    print(f"  {label}: {len(ranked)} brani, {len(dates_sorted)} giorni")
    return ranked, dates_sorted

print("Elaborazione Radio Mitology...")
mitology_ranked, mitology_dates_sorted = process_generic_radio(mitology_history, "Mitology")

print("Elaborazione Radio Nostalgia Toscana...")
nostalgia_ranked, nostalgia_dates_sorted = process_generic_radio(nostalgia_history, "Nostalgia")

print("Elaborazione Radio Toscana...")
toscana_ranked, toscana_dates_sorted = process_generic_radio(toscana_history, "Toscana")

print("Elaborazione Radio Italia...")
italia_ranked, italia_dates_sorted = process_generic_radio(italia_history, "Radio Italia")

print("Elaborazione RDS...")
rds_ranked, rds_dates_sorted = process_generic_radio(rds_history, "RDS")

print("Elaborazione RTL 102.5...")
rtl1025_ranked, rtl1025_dates_sorted = process_generic_radio(rtl1025_history, "RTL 102.5")

# ── Serializza JSON per HTML ──────────────────────────────────────────────────
def make_radio_data(ranked, dates_sorted):
    songs_out = []
    for s in ranked:
        key = (s['artist'] + '|' + s['title']).lower()
        song = {
            'artist': s['artist'],
            'title': s['title'],
            'year': s['year'],
            'radioDate': s.get('radioDate', 'N/A'),
            'total': s['total'],
            'rank': s['rank'],
            'days': s['days'],  # {date: [time, ...]}
        }
        # Incorpora URL anteprima: solo URL iTunes (permanenti).
        # URL Deezer scadono dopo 2-3 giorni → il JS le recupera live via JSONP.
        # None  = cercato ma non trovato su nessun portale (JS non riproverà)
        # URL   = iTunes trovato (permanente, JS suona direttamente senza API call)
        # assente = non in cache o Deezer (JS farà ricerca live iTunes+Deezer JSONP)
        if key in preview_cache:
            cached_url = preview_cache[key]
            is_itunes = cached_url and 'apple.com' in cached_url
            if is_itunes:
                song['previewUrl'] = cached_url   # iTunes: incorpora, non scade
            elif cached_url is None:
                song['previewUrl'] = None          # Cercato, non trovato: JS non riprova
            # Deezer (o stringa 'null'): lascia assente → JS ricerca live
        songs_out.append(song)
    return {
        'songs': songs_out,
        'dates': dates_sorted
    }

raw_subasio   = make_radio_data(subasio_ranked,   subasio_dates_sorted)
raw_divina    = make_radio_data(divina_ranked,    divina_dates_sorted)
raw_mitology  = make_radio_data(mitology_ranked,  mitology_dates_sorted)
raw_nostalgia = make_radio_data(nostalgia_ranked, nostalgia_dates_sorted)
raw_toscana   = make_radio_data(toscana_ranked,   toscana_dates_sorted)
raw_italia    = make_radio_data(italia_ranked,    italia_dates_sorted)
raw_rds       = make_radio_data(rds_ranked,       rds_dates_sorted)
raw_rtl1025   = make_radio_data(rtl1025_ranked,   rtl1025_dates_sorted)

# Tenta di caricare le classifiche calcolate su Google Sheets
try:
    from google_sheets_sync import upload_rankings
    all_data_to_upload = {
        'subasio': raw_subasio,
        'divina': raw_divina,
        'mitology': raw_mitology,
        'nostalgia': raw_nostalgia,
        'toscana': raw_toscana,
        'italia': raw_italia,
        'rds': raw_rds,
        'rtl1025': raw_rtl1025
    }
    upload_rankings(all_data_to_upload)
except Exception as e:
    print(f"  [GOOGLE SHEETS] Impossibile caricare le classifiche: {e}")

json_subasio   = json.dumps(raw_subasio,   ensure_ascii=False, separators=(',', ':'))
json_divina    = json.dumps(raw_divina,    ensure_ascii=False, separators=(',', ':'))
json_mitology  = json.dumps(raw_mitology,  ensure_ascii=False, separators=(',', ':'))
json_nostalgia = json.dumps(raw_nostalgia, ensure_ascii=False, separators=(',', ':'))
json_toscana   = json.dumps(raw_toscana,   ensure_ascii=False, separators=(',', ':'))
json_italia    = json.dumps(raw_italia,    ensure_ascii=False, separators=(',', ':'))
json_rds       = json.dumps(raw_rds,       ensure_ascii=False, separators=(',', ':'))
json_rtl1025   = json.dumps(raw_rtl1025,   ensure_ascii=False, separators=(',', ':'))

print(f"  JSON Subasio:   {len(json_subasio)//1024} KB")
print(f"  JSON Divina:    {len(json_divina)//1024} KB")
print(f"  JSON Mitology:  {len(json_mitology)//1024} KB")
print(f"  JSON Nostalgia: {len(json_nostalgia)//1024} KB")
print(f"  JSON Toscana:   {len(json_toscana)//1024} KB")
print(f"  JSON Italia:    {len(json_italia)//1024} KB")
print(f"  JSON RDS:       {len(json_rds)//1024} KB")
print(f"  JSON RTL 102.5: {len(json_rtl1025)//1024} KB")

# ── Genera HTML ───────────────────────────────────────────────────────────────
print("Generazione HTML...")

today_str = datetime.now().strftime("%d/%m/%Y %H:%M")

html = f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Radio Charts – Classifica Airplay</title>
<style>
:root{{
  --red:#C8102E; --red-dark:#9e0c24; --gold:#FFD700; --silver:#C0C0C0; --bronze:#CD7F32;
  --bg:#f4f5f7; --surface:#fff; --border:#e0e0e0;
  --text:#1a1a2e; --text-muted:#666; --text-light:#999;
  --up:#00a550; --down:#C8102E; --new:#0057b8; --stable:#888;
  --top10:#fff3cd; --top3-bg:#fff;
}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Segoe UI',system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--text);min-height:100vh}}

/* HEADER */
header{{background:linear-gradient(135deg,#1a1a2e 0%,#16213e 60%,#0f3460 100%);color:#fff;padding:0;box-shadow:0 4px 20px rgba(0,0,0,.4)}}
.header-top{{display:flex;align-items:center;justify-content:space-between;padding:18px 32px 12px}}
.logo{{display:flex;align-items:center;gap:12px}}
.logo-icon{{width:44px;height:44px;background:var(--red);border-radius:10px;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:20px;letter-spacing:-1px;color:#fff}}
.logo-text h1{{font-size:22px;font-weight:800;letter-spacing:.5px}}
.logo-text span{{font-size:11px;opacity:.6;text-transform:uppercase;letter-spacing:2px}}
.header-meta{{text-align:right;font-size:12px;opacity:.6}}
.header-meta strong{{display:block;font-size:14px;opacity:1;color:var(--gold)}}

/* RADIO TABS */
.radio-tabs{{display:flex;padding:0 32px;border-top:1px solid rgba(255,255,255,.1);overflow-x:auto;white-space:nowrap;-webkit-overflow-scrolling:touch}}
.radio-tabs::-webkit-scrollbar{{display:none}}
.radio-tab{{padding:14px 28px;font-size:14px;font-weight:600;cursor:pointer;border:none;background:transparent;color:rgba(255,255,255,.5);border-bottom:3px solid transparent;transition:all .2s;letter-spacing:.5px;text-transform:uppercase;flex-shrink:0}}
.radio-tab:hover{{color:rgba(255,255,255,.85)}}
.radio-tab.active{{color:#fff;border-bottom-color:var(--red)}}

/* FILTERS */
.filters-bar{{background:#fff;border-bottom:2px solid var(--border);padding:16px 32px;display:flex;flex-direction:column;gap:12px;box-shadow:0 2px 8px rgba(0,0,0,.06)}}
.filter-row{{display:flex;align-items:center;gap:16px;width:100%}}
.main-filter-row{{justify-content:space-between}}
.search-box{{position:relative;flex:1;max-width:400px}}
.search-box input{{width:100%;padding:9px 36px 9px 14px;border:1.5px solid var(--border);border-radius:8px;font-size:14px;outline:none;transition:border-color .2s;background:#fafafa}}
.search-box input:focus{{border-color:var(--red);background:#fff}}
.search-box .icon{{position:absolute;right:11px;top:50%;transform:translateY(-50%);color:var(--text-muted);font-size:15px;pointer-events:none}}
.chips-filter-row{{overflow:hidden}}
.decade-chips{{display:flex;gap:6px;overflow-x:auto;white-space:nowrap;padding-bottom:4px;-webkit-overflow-scrolling:touch}}
.decade-chips::-webkit-scrollbar{{display:none}}
.chip{{flex-shrink:0;padding:6px 13px;border-radius:20px;font-size:12px;font-weight:600;cursor:pointer;border:1.5px solid var(--border);background:#fafafa;color:var(--text-muted);transition:all .2s}}
.chip:hover{{border-color:var(--red);color:var(--red)}}
.chip.active{{background:var(--red);color:#fff;border-color:var(--red)}}
.dropdowns-filter-row{{gap:24px}}
.filter-select-group{{display:flex;align-items:center;gap:8px}}
.filter-input-group{{display:flex;align-items:center;gap:8px}}
.filter-input{{width:70px;padding:8px 10px;border:1.5px solid var(--border);border-radius:8px;font-size:13px;background:#fafafa;outline:none;color:var(--text);transition:border-color .2s}}
.filter-input:focus{{border-color:var(--red);background:#fff}}
.results-count-wrap{{margin-left:auto}}
.results-count{{font-size:13px;color:var(--text-muted);white-space:nowrap}}
.filter-label{{font-size:12px;color:var(--text-muted);font-weight:600;text-transform:uppercase;letter-spacing:.5px;white-space:nowrap}}

/* TOGGLE SWITCH STYLE */
.toggle-wrap {{
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
  font-size: 11px;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-right: 14px;
}}
.toggle-switch {{
  position: relative;
  width: 36px;
  height: 20px;
  background: #cbd5e1;
  border-radius: 20px;
  transition: background-color 0.2s;
}}
.toggle-switch::after {{
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 16px;
  height: 16px;
  background: #fff;
  border-radius: 50%;
  box-shadow: 0 1px 3px rgba(0,0,0,0.15);
  transition: transform 0.2s;
}}
.toggle-wrap input {{
  display: none;
}}
.toggle-wrap input:checked + .toggle-switch {{
  background: var(--red);
}}
.toggle-wrap input:checked + .toggle-switch::after {{
  transform: translateX(16px);
}}

/* DECADE CHIPS */
.decade-chips{{display:flex;gap:6px;flex-wrap:wrap}}
.chip{{padding:6px 13px;border-radius:20px;font-size:12px;font-weight:600;cursor:pointer;border:1.5px solid var(--border);background:#fafafa;color:var(--text-muted);transition:all .2s;white-space:nowrap}}
.chip:hover{{border-color:var(--red);color:var(--red)}}
.chip.active{{background:var(--red);color:#fff;border-color:var(--red)}}

/* DATE FILTER */
.date-filter-wrap{{position:relative}}
.date-filter-btn{{
  padding:6px 13px;border-radius:20px;font-size:12px;font-weight:600;
  cursor:pointer;border:1.5px solid var(--border);background:#fafafa;
  color:var(--text-muted);transition:all .2s;white-space:nowrap;
}}
.date-filter-btn.active{{background:var(--red);color:#fff;border-color:var(--red)}}
.date-panel{{
  display:none;position:absolute;top:calc(100% + 6px);left:0;z-index:200;
  background:#fff;border:1.5px solid var(--border);border-radius:12px;
  box-shadow:0 8px 32px rgba(0,0,0,.15);padding:14px;min-width:260px;
}}
.date-panel.open{{display:block}}
/* HOUR FILTER */
.hour-filter-wrap{{position:relative}}
.hour-filter-btn{{
  padding:6px 13px;border-radius:20px;font-size:12px;font-weight:600;
  cursor:pointer;border:1.5px solid var(--border);background:#fafafa;
  color:var(--text-muted);transition:all .2s;white-space:nowrap;
}}
.hour-filter-btn.active{{background:var(--red);color:#fff;border-color:var(--red)}}
.hour-panel{{
  display:none;position:absolute;top:calc(100% + 6px);left:0;z-index:200;
  background:#fff;border:1.5px solid var(--border);border-radius:12px;
  box-shadow:0 8px 32px rgba(0,0,0,.15);padding:14px;min-width:320px;
}}
.hour-panel.open{{display:block}}
.hour-grid{{
  display:grid;grid-template-columns:repeat(6,1fr);gap:8px;margin-top:10px;
}}
.hour-cb-wrap{{
  display:flex;align-items:center;justify-content:center;
  gap:4px;padding:6px 4px;border-radius:6px;font-size:12px;font-weight:600;
  border:1px solid var(--border);background:#fafafa;color:var(--text-muted);
  cursor:pointer;user-select:none;transition:all .15s;
}}
.hour-cb-wrap input[type="checkbox"]{{
  accent-color:var(--red);cursor:pointer;margin:0;
}}
.hour-cb-wrap:hover{{
  border-color:var(--red);color:var(--red);background:rgba(200,16,46,0.04);
}}
.hour-cb-wrap.active{{
  background:rgba(200,16,46,0.08);border-color:var(--red);color:var(--text);
}}
/* Preset rapidi */
.cal-shortcuts{{display:flex;gap:5px;flex-wrap:wrap;margin-bottom:10px;padding-bottom:10px;border-bottom:1px solid var(--border)}}
.cal-shortcut-btn{{
  padding:4px 10px;font-size:11px;font-weight:600;cursor:pointer;
  border:1.5px solid var(--border);border-radius:20px;background:#f5f5f5;
  color:var(--text-muted);transition:all .15s;white-space:nowrap;
}}
.cal-shortcut-btn:hover,.cal-shortcut-btn.active{{background:var(--red);color:#fff;border-color:var(--red)}}
/* Navigazione mese */
.cal-nav{{display:flex;align-items:center;justify-content:space-between;margin-bottom:8px}}
.cal-nav-btn{{
  width:26px;height:26px;border:1.5px solid var(--border);border-radius:6px;
  background:#f5f5f5;cursor:pointer;font-size:14px;font-weight:700;
  display:flex;align-items:center;justify-content:center;color:var(--text);transition:all .15s;
}}
.cal-nav-btn:hover{{background:var(--red);color:#fff;border-color:var(--red)}}
.cal-month-label{{font-size:13px;font-weight:700;color:var(--text)}}
/* Griglia calendario */
.cal-grid{{display:grid;grid-template-columns:repeat(7,1fr);gap:2px}}
.cal-head{{text-align:center;font-size:10px;font-weight:700;color:var(--text-muted);
  padding:3px 0;text-transform:uppercase;letter-spacing:.3px}}
.cal-cell{{
  text-align:center;font-size:12px;font-weight:500;padding:5px 2px;
  border-radius:6px;color:var(--text-muted);min-width:0;
}}
.cal-cell.has-data{{
  cursor:pointer;color:var(--text);font-weight:600;
  background:#f0f4ff;
}}
.cal-cell.has-data:hover{{background:#dde4ff}}
.cal-cell.has-data.selected{{background:var(--red);color:#fff}}
.cal-cell.empty{{visibility:hidden}}
.cal-cell.no-data{{color:#ccc;cursor:default}}

/* STATS STRIP */
.stats-strip{{display:flex;gap:0;background:var(--surface);border-bottom:1px solid var(--border)}}
.stat-chip{{flex:1;padding:12px 20px;text-align:center;border-right:1px solid var(--border)}}
.stat-chip:last-child{{border-right:none}}
.stat-chip .val{{font-size:20px;font-weight:800;color:var(--red)}}
.stat-chip .lbl{{font-size:10px;text-transform:uppercase;letter-spacing:1px;color:var(--text-muted);margin-top:2px}}

/* MAIN TABLE */
.table-wrap{{padding:24px 32px;overflow-x:auto}}
table{{width:100%;border-collapse:collapse;font-size:14px}}
thead tr{{background:linear-gradient(135deg,#1a1a2e,#16213e);color:#fff}}
thead th{{padding:12px 16px;text-align:left;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.8px;white-space:nowrap;cursor:pointer;user-select:none;transition:background .15s}}
thead th:hover{{background:rgba(255,255,255,.08)}}
thead th.sorted-asc::after{{content:' ▲';color:var(--gold)}}
thead th.sorted-desc::after{{content:' ▼';color:var(--gold)}}
thead th.sorted-asc.sorted-multi::after{{content:' ▲' attr(data-sort-index);font-size:10px;color:#bbb;margin-left:2px}}
thead th.sorted-desc.sorted-multi::after{{content:' ▼' attr(data-sort-index);font-size:10px;color:#bbb;margin-left:2px}}
thead th:first-child,thead th:nth-child(2){{cursor:default}}
tbody tr{{border-bottom:1px solid var(--border);transition:background .15s;background:var(--surface)}}
tbody tr:hover{{background:#f0f4ff}}
tbody tr.top1{{background:linear-gradient(90deg,#fffbea,#fff)}}
tbody tr.top2{{background:linear-gradient(90deg,#f8f8f8,#fff)}}
tbody tr.top3{{background:linear-gradient(90deg,#fff5ee,#fff)}}
td{{padding:10px 16px;vertical-align:middle}}

/* POSITION */
.pos-cell{{text-align:center;width:52px}}
.pos-badge{{width:36px;height:36px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-size:13px;font-weight:900;margin:0 auto}}
.pos-1{{background:linear-gradient(135deg,#FFD700,#FFA500);color:#7a4600;box-shadow:0 2px 8px rgba(255,165,0,.4)}}
.pos-2{{background:linear-gradient(135deg,#D0D0D0,#A0A0A0);color:#444;box-shadow:0 2px 6px rgba(0,0,0,.2)}}
.pos-3{{background:linear-gradient(135deg,#CD8B4A,#A0522D);color:#fff;box-shadow:0 2px 6px rgba(139,69,19,.3)}}
.pos-top10{{background:#1a1a2e;color:#fff;font-size:12px}}
.pos-rest{{background:#f0f0f0;color:var(--text-muted);font-size:12px}}

/* TREND */
.trend-cell{{width:38px;text-align:center}}
.trend{{font-size:11px;font-weight:700;padding:3px 5px;border-radius:4px;display:inline-block}}
.trend-up{{color:var(--up);background:#e8f5e9}}
.trend-down{{color:var(--down);background:#ffebee}}
.trend-new{{color:var(--new);background:#e3f2fd;font-size:10px;letter-spacing:.5px}}
.trend-stable{{color:var(--stable);background:#f5f5f5}}

/* SONG INFO */
.song-artist{{font-weight:700;font-size:14px;color:var(--text)}}
.song-title{{font-size:13px;color:var(--text-muted);margin-top:2px}}
.song-year{{display:inline-block;background:#e8eaf6;color:#3949ab;font-size:10px;font-weight:700;padding:2px 7px;border-radius:10px;margin-left:6px;vertical-align:middle;letter-spacing:.5px}}

/* PLAYS */
.plays-cell{{text-align:center;width:80px;cursor:pointer}}
.plays-num{{font-size:18px;font-weight:900;color:var(--red);transition:transform .15s}}
.plays-num:hover{{transform:scale(1.15)}}
.plays-lbl{{font-size:10px;color:var(--text-muted);text-transform:uppercase}}
.plays-cell:hover .plays-num{{color:var(--red-dark)}}

/* META */
.meta-cell{{text-align:center;width:70px}}
.meta-val{{font-size:15px;font-weight:700;color:var(--text)}}
.meta-lbl{{font-size:10px;color:var(--text-muted);text-transform:uppercase;letter-spacing:.5px}}

/* PLAY BUTTON */
.play-btn{{
  display:inline-flex;align-items:center;justify-content:center;
  width:26px;height:26px;border-radius:50%;border:none;cursor:pointer;
  background:var(--red);color:#fff;font-size:11px;flex-shrink:0;
  transition:all .2s;line-height:1;padding:0;
}}
.play-btn:hover{{background:var(--red-dark);transform:scale(1.12)}}
.play-btn.loading{{background:#aaa;animation:pulse .7s infinite alternate;cursor:wait}}
.play-btn.playing{{background:#00a550}}
.play-btn.no-preview{{background:#ccc;cursor:not-allowed;color:#888}}
.play-btn-lg{{width:34px;height:34px;font-size:14px}}
@keyframes pulse{{from{{opacity:.5}}to{{opacity:1}}}}

/* EMPTY STATE */
.empty-state{{text-align:center;padding:60px 20px;color:var(--text-muted)}}
.empty-state .icon{{font-size:48px;margin-bottom:12px}}

/* RESPONSIVE */
@media(max-width:768px){{
  .header-top{{padding:14px 16px 10px}}
  .filters-bar{{
    padding:12px 16px;
    gap:10px;
  }}
  .filter-row{{
    flex-wrap: nowrap;
    gap: 8px;
  }}
  .main-filter-row{{
    flex-wrap: nowrap;
  }}
  .search-box{{
    max-width: none;
  }}
  .export-btn{{
    padding: 9px 12px !important;
    font-size: 12px !important;
    margin-left: 0 !important;
  }}
  .dropdowns-filter-row{{
    gap: 12px;
    justify-content: space-between;
  }}
  .filter-select-group{{
    flex: 1;
    justify-content: flex-start;
  }}
  .date-filter-btn, .hour-filter-btn{{
    width: 100%;
    text-align: left;
    padding: 8px 10px !important;
  }}
  .controls-filter-row{{
    justify-content: space-between;
    align-items: center;
    gap: 6px;
  }}
  .toggle-wrap{{
    margin-right: 0 !important;
    font-size: 10px !important;
    gap: 4px !important;
  }}
  .toggle-switch{{
    width: 32px !important;
    height: 18px !important;
  }}
  .toggle-switch::after{{
    width: 14px !important;
    height: 14px !important;
  }}
  .toggle-wrap input:checked + .toggle-switch::after{{
    transform: translateX(14px);
  }}
  .filter-input-group{{
    gap: 4px;
  }}
  .filter-input-group .filter-label{{
    font-size: 10px !important;
  }}
  .filter-input{{
    width: 50px !important;
    padding: 6px 6px !important;
    font-size: 12px !important;
  }}
  .results-count-wrap{{
    margin-left: 0;
  }}
  .results-count{{
    font-size: 11px !important;
  }}
  
  .table-wrap{{padding:12px 8px}}
  .meta-cell{{display:none}}
  
  .radio-tabs{{
    padding:0 16px;
    overflow-x: auto;
    white-space: nowrap;
    -webkit-overflow-scrolling: touch;
  }}
  .radio-tabs::-webkit-scrollbar{{
    display: none;
  }}
  .radio-tab{{
    padding: 12px 16px;
    font-size: 12px;
    flex-shrink: 0;
  }}
  
  /* Tabella Mobile */
  td{{
    padding: 8px 8px !important;
  }}
  .pos-cell{{
    width: 40px;
  }}
  .pos-badge{{
    width: 28px !important;
    height: 28px !important;
    font-size: 11px !important;
  }}
  .trend-cell{{
    width: 32px;
  }}
  .trend{{
    font-size: 9px !important;
    padding: 2px 4px !important;
  }}
  .song-artist{{
    font-size: 13px !important;
  }}
  .song-title{{
    font-size: 11px !important;
  }}
  .radio-date-cell{{
    width: 95px !important;
  }}
  .radio-date-badge{{
    font-size: 9px !important;
    padding: 2px 6px !important;
  }}
  .plays-cell{{
    width: 65px;
  }}
  .plays-num{{
    font-size: 15px !important;
  }}
  .play-btn{{
    width: 22px !important;
    height: 22px !important;
    font-size: 9px !important;
  }}
}}

@media(max-width:480px){{
  .login-box{{
    padding: 32px 20px;
    border-radius: 16px;
  }}
  .logo-text h1{{
    font-size: 18px;
  }}
  .logo-icon{{
    width: 36px;
    height: 36px;
    font-size: 16px;
  }}
}}

/* ── MODAL POPUP ─────────────────────────────────────────────── */
.modal-overlay{{
  display:none;position:fixed;inset:0;background:rgba(0,0,0,.55);
  z-index:1000;align-items:center;justify-content:center;
  animation:fadeIn .18s ease;
}}
.modal-overlay.open{{display:flex}}
@keyframes fadeIn{{from{{opacity:0}}to{{opacity:1}}}}

.modal{{
  background:#fff;border-radius:14px;box-shadow:0 12px 48px rgba(0,0,0,.28);
  width:min(520px,92vw);max-height:80vh;display:flex;flex-direction:column;
  animation:slideUp .2s ease;
}}
@keyframes slideUp{{from{{transform:translateY(20px);opacity:0}}to{{transform:translateY(0);opacity:1}}}}

.modal-header{{
  padding:20px 24px 14px;border-bottom:1px solid var(--border);display:flex;
  align-items:flex-start;justify-content:space-between;gap:12px;
}}
.modal-title{{flex:1}}
.modal-artist{{font-size:15px;font-weight:800;color:var(--text)}}
.modal-song{{font-size:13px;color:var(--text-muted);margin-top:3px}}
.modal-close{{
  background:none;border:none;font-size:22px;cursor:pointer;color:var(--text-muted);
  line-height:1;padding:2px 6px;border-radius:6px;transition:background .15s;flex-shrink:0;
}}
.modal-close:hover{{background:#f0f0f0;color:var(--text)}}

.modal-body{{overflow-y:auto;padding:16px 24px 20px;flex:1}}
.modal-total{{
  display:inline-flex;align-items:center;gap:8px;background:#fff1f2;
  border:1px solid #ffd0d5;border-radius:8px;padding:8px 14px;margin-bottom:16px;
  font-size:14px;color:var(--red);font-weight:700;
}}

.day-block{{margin-bottom:14px}}
.day-header{{
  display:flex;align-items:center;gap:8px;margin-bottom:6px;
}}
.day-date{{
  font-size:12px;font-weight:700;color:var(--text);background:#f0f4ff;
  border-radius:6px;padding:3px 9px;letter-spacing:.4px;
}}
.day-count{{font-size:11px;color:var(--text-muted);}}
.times-list{{display:flex;flex-wrap:wrap;gap:6px}}
.time-chip{{
  background:#f8f9fa;border:1px solid var(--border);border-radius:6px;
  padding:4px 10px;font-size:13px;color:var(--text);font-family:monospace;
  font-weight:600;letter-spacing:.3px;
}}
.time-chip.live{{background:#fff3cd;border-color:#ffc107;color:#856404}}

/* Modal tabs */
.modal-tabs{{display:flex;border-bottom:2px solid var(--border);padding:0 24px;gap:0}}
.modal-tab-btn{{padding:10px 18px;font-size:13px;font-weight:600;cursor:pointer;border:none;background:transparent;color:var(--text-muted);border-bottom:3px solid transparent;margin-bottom:-2px;transition:all .2s}}
.modal-tab-btn:hover{{color:var(--text)}}
.modal-tab-btn.active{{color:var(--red);border-bottom-color:var(--red)}}
.modal-tab-pane{{display:none}}
.modal-tab-pane.active{{display:block}}

/* Artist songs in popup */
.artist-song-card{{border:1px solid var(--border);border-radius:10px;margin-bottom:12px;overflow:hidden}}
.artist-song-header{{
  display:flex;align-items:center;justify-content:space-between;
  padding:10px 14px;background:#f8f9fa;cursor:pointer;
  transition:background .15s;gap:10px;
}}
.artist-song-header:hover{{background:#eef0f8}}
.artist-song-name{{font-size:13px;font-weight:700;color:var(--text);flex:1}}
.artist-song-total{{background:var(--red);color:#fff;font-size:11px;font-weight:800;padding:3px 9px;border-radius:10px;white-space:nowrap}}
.artist-song-toggle{{font-size:11px;color:var(--text-muted);transition:transform .2s}}
.artist-song-body{{display:none;padding:12px 14px;border-top:1px solid var(--border);background:#fff}}

/* Glassmorphism & Sleek styling for Edit Modal */
.modal-overlay{{
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  background: rgba(15, 23, 42, 0.45);
}}

.edit-modal{{
  background: rgba(255, 255, 255, 0.85) !important;
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.4);
  border-radius: 20px !important;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.15) !important;
  overflow: hidden;
  max-width: 420px !important;
}}

.edit-modal-title-text{{
  font-size: 18px;
  font-weight: 800;
  color: #1e293b;
  letter-spacing: -0.3px;
}}

.edit-modal-subtitle{{
  font-size: 13px;
  color: #64748b;
  margin-top: 6px;
  line-height: 1.4;
}}

.bold-text{{
  font-weight: 700;
  color: #334155;
}}

.edit-modal-body{{
  padding: 24px !important;
}}

.edit-input-label{{
  display: block;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #64748b;
  margin-bottom: 8px;
}}

.input-with-icon{{
  position: relative;
  margin-bottom: 24px;
}}

.input-icon{{
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 16px;
  pointer-events: none;
}}

.edit-year-input-field{{
  width: 100%;
  padding: 12px 14px 12px 42px;
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  background: rgba(255, 255, 255, 0.6);
  border: 1.5px solid #cbd5e1;
  border-radius: 12px;
  outline: none;
  transition: all 0.25s ease;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.02);
}}

.edit-year-input-field:focus{{
  border-color: #00a550;
  background: #fff;
  box-shadow: 0 0 0 4px rgba(0, 165, 80, 0.12), inset 0 2px 4px rgba(0, 0, 0, 0.02);
}}

.edit-year-input-field:disabled{{
  background: rgba(241, 245, 249, 0.6);
  color: #94a3b8;
  border-color: #e2e8f0;
  cursor: not-allowed;
}}

.edit-modal-actions{{
  display: flex;
  gap: 12px;
  margin-top: 8px;
}}

.edit-btn{{
  flex: 1;
  padding: 12px 20px;
  font-size: 14px;
  font-weight: 700;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  outline: none;
  text-align: center;
}}

.edit-btn-cancel{{
  background: transparent;
  color: #64748b;
  border: 1.5px solid #cbd5e1;
}}

.edit-btn-cancel:hover:not(:disabled){{
  background: rgba(100, 116, 139, 0.08);
  border-color: #94a3b8;
  color: #334155;
}}

.edit-btn-save{{
  background: #00a550;
  color: #fff;
  border: none;
  box-shadow: 0 4px 12px rgba(0, 165, 80, 0.2);
}}

.edit-btn-save:hover:not(:disabled){{
  background: #008f45;
  transform: scale(1.03);
  box-shadow: 0 6px 16px rgba(0, 165, 80, 0.3);
}}

.edit-btn-save:active:not(:disabled){{
  transform: scale(0.98);
}}

.edit-btn-search{{
  background: #0284c7;
  color: #fff;
  border: none;
  box-shadow: 0 4px 12px rgba(2,132,199,0.25);
  margin-bottom: 20px;
  width: 100%;
}}

.edit-btn-search:hover:not(:disabled){{
  background: #0369a1;
  transform: scale(1.02);
  box-shadow: 0 6px 16px rgba(2,132,199,0.35);
}}

.edit-btn-search:active:not(:disabled){{
  transform: scale(0.98);
}}

.edit-btn:disabled{{
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
  box-shadow: none !important;
}}

/* Interactive Year Badges styling */
.song-year{{
  display: inline-flex !important;
  align-items: center;
  gap: 4px;
  background: rgba(57, 73, 171, 0.08) !important;
  color: #3949ab !important;
  font-size: 11px !important;
  font-weight: 700 !important;
  padding: 3px 8px !important;
  border-radius: 6px !important;
  margin-left: 8px !important;
  vertical-align: middle;
  cursor: pointer;
  transition: all 0.2s ease !important;
  border: 1px solid rgba(57, 73, 171, 0.15) !important;
}}

.song-year:hover{{
  background: rgba(57, 73, 171, 0.16) !important;
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(57, 73, 171, 0.15);
}}

.song-year.na{{
  background: rgba(102, 102, 102, 0.06) !important;
  color: #666 !important;
  border: 1px dashed rgba(102, 102, 102, 0.2) !important;
}}

.song-year.na:hover{{
  background: rgba(102, 102, 102, 0.12) !important;
  border-style: solid !important;
}}

/* Radio Date styling */
.radio-date-cell {{
  text-align: center !important;
  width: 120px !important;
}}
.radio-date-badge {{
  display: inline-flex !important;
  align-items: center;
  gap: 5px;
  background: rgba(13, 148, 136, 0.08) !important;
  color: #0d9488 !important;
  font-size: 11px !important;
  font-weight: 700 !important;
  padding: 3px 8px !important;
  border-radius: 6px !important;
  cursor: pointer;
  transition: all 0.2s ease !important;
  border: 1px solid rgba(13, 148, 136, 0.15) !important;
}}
.radio-date-badge:hover {{
  background: rgba(13, 148, 136, 0.16) !important;
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(13, 148, 136, 0.15);
}}
.radio-date-badge.na {{
  background: rgba(102, 102, 102, 0.06) !important;
  color: #666 !important;
  border: 1px dashed rgba(102, 102, 102, 0.2) !important;
}}
.radio-date-badge.na:hover {{
  background: rgba(102, 102, 102, 0.12) !important;
  border-style: solid !important;
}}
.radio-date-badge svg {{
  width: 10px;
  height: 10px;
  fill: currentColor;
  opacity: 0.65;
}}

/* Error Banner */
.edit-error-banner{{
  background: #fef2f2;
  border: 1px solid #fee2e2;
  border-radius: 12px;
  color: #991b1b;
  padding: 12px 16px;
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 20px;
  line-height: 1.4;
  animation: shake 0.4s ease;
}}

@keyframes shake{{
  0%, 100%{{ transform: translateX(0); }}
  25%{{ transform: translateX(-6px); }}
  75%{{ transform: translateX(6px); }}
}}

/* Success Banner & Checkmark Animation */
.edit-success-banner{{
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 16px;
  color: #065f46;
  font-size: 15px;
  font-weight: 700;
}}

.checkmark-wrapper{{
  width: 56px;
  height: 56px;
}}

.checkmark{{
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: block;
  stroke-width: 2;
  stroke: #00a550;
  stroke-miterlimit: 10;
  box-shadow: inset 0px 0px 0px #00a550;
  animation: fill .4s ease-in-out .4s forwards, scale .3s ease-in-out .9s both;
}}

.checkmark__circle{{
  stroke-dasharray: 166;
  stroke-dashoffset: 166;
  stroke-width: 2;
  stroke-miterlimit: 10;
  stroke: #00a550;
  fill: none;
  animation: stroke .6s cubic-bezier(0.650, 0.000, 0.450, 1.000) forwards;
}}

.checkmark__check{{
  transform-origin: 50% 50%;
  stroke-dasharray: 48;
  stroke-dashoffset: 48;
  animation: stroke .3s cubic-bezier(0.650, 0.000, 0.450, 1.000) .8s forwards;
}}

@keyframes stroke{{
  100%{{ stroke-dashoffset: 0; }}
}}

@keyframes fill{{
  100%{{ box-shadow: inset 0px 0px 0px 30px rgba(0, 165, 80, 0.1); }}
}}

/* CLASSIFICA GLOBALE & SELEZIONE RADIO */
.global-selector-bar {{
  display: none;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px) saturate(180%);
  -webkit-backdrop-filter: blur(12px) saturate(180%);
  border-bottom: 1.5px solid var(--border);
  padding: 16px 32px;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}}
.global-selector-bar.show {{
  display: flex;
}}
.global-selector-label {{
  font-size: 13px;
  font-weight: 700;
  color: var(--text);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}}
.global-checkboxes {{
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}}
.global-cb-wrap {{
  display: inline-flex;
  align-items: center;
  cursor: pointer;
  user-select: none;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-muted);
  background: #f1f5f9;
  border: 1.5px solid #cbd5e1;
  border-radius: 20px;
  padding: 6px 14px;
  transition: all 0.2s ease;
}}
.global-cb-wrap input[type="checkbox"] {{
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}}
.global-cb-check {{
  width: 14px;
  height: 14px;
  border: 1.5px solid #94a3b8;
  border-radius: 4px;
  margin-right: 8px;
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  background: #fff;
}}
.global-cb-wrap input:checked + .global-cb-check {{
  background: #0d9488;
  border-color: #0d9488;
}}
.global-cb-wrap input:checked + .global-cb-check::after {{
  content: '✓';
  color: #fff;
  font-size: 10px;
  font-weight: bold;
  position: absolute;
}}
.global-cb-wrap:hover {{
  border-color: #0d9488;
  color: #0d9488;
  background: rgba(13, 148, 136, 0.04);
}}
.global-cb-wrap.checked {{
  border-color: #0d9488;
  color: #0d9488;
  background: rgba(13, 148, 136, 0.08);
}}
.global-actions {{
  display: flex;
  gap: 8px;
  margin-left: auto;
}}
.global-action-btn {{
  padding: 5px 12px;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
  border: 1.5px solid #cbd5e1;
  border-radius: 20px;
  background: #fff;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  transition: all 0.15s ease;
}}
.global-action-btn:hover {{
  border-color: #0d9488;
  color: #0d9488;
  background: rgba(13, 148, 136, 0.04);
}}
.export-btn {{
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #0d9488;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 9px 16px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 4px 12px rgba(13, 148, 136, 0.25);
  margin-left: 8px;
}}
.export-btn:hover {{
  background: #0f766e;
  box-shadow: 0 6px 16px rgba(13, 148, 136, 0.35);
  transform: translateY(-1px);
}}
.export-btn:active {{
  transform: translateY(0);
}}
.radio-tab.globale {{
  color: #fef08a !important;
  border-bottom-color: transparent !important;
}}
.radio-tab.globale:hover {{
  color: #fef9c3 !important;
}}
.radio-tab.globale.active {{
  color: #facc15 !important;
  border-bottom-color: #facc15 !important;
}}
.radio-source-tag {{
  display: inline-block;
  font-size: 9px;
  font-weight: 800;
  text-transform: uppercase;
  background: rgba(15, 23, 42, 0.08);
  color: #475569;
  border-radius: 4px;
  padding: 1px 4px;
  margin-left: 6px;
  letter-spacing: 0.3px;
  vertical-align: middle;
}}

/* LOGIN OVERLAY & SLEEK GLASSMORPHISM */
.login-overlay {{
  position: fixed;
  inset: 0;
  background: radial-gradient(circle at center, #1e293b 0%, #0f172a 100%);
  z-index: 5000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}}
.login-box {{
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 24px;
  width: min(400px, 100%);
  padding: 40px 32px;
  text-align: center;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  color: #fff;
  animation: slideUp 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}}
.login-logo {{
  font-size: 48px;
  margin-bottom: 16px;
  animation: pulse 2s infinite ease-in-out;
}}
.login-box h2 {{
  font-size: 26px;
  font-weight: 800;
  letter-spacing: -0.5px;
  margin-bottom: 8px;
}}
.login-box p {{
  color: #94a3b8;
  font-size: 14px;
  margin-bottom: 32px;
}}
.login-error {{
  background: rgba(239, 68, 68, 0.15);
  border: 1.5px solid rgba(239, 68, 68, 0.3);
  color: #fca5a5;
  border-radius: 12px;
  padding: 12px;
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 20px;
  text-align: left;
}}
.input-wrap {{
  position: relative;
  margin-bottom: 18px;
}}
.input-wrap .input-icon {{
  position: absolute;
  left: 16px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 16px;
  color: #94a3b8;
}}
.input-wrap input {{
  width: 100%;
  padding: 14px 16px 14px 46px;
  background: rgba(255, 255, 255, 0.05);
  border: 1.5px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  color: #fff;
  font-size: 15px;
  font-weight: 500;
  outline: none;
  transition: all 0.2s ease;
}}
.input-wrap input:focus {{
  border-color: var(--red);
  background: rgba(255, 255, 255, 0.08);
  box-shadow: 0 0 0 4px rgba(200, 16, 46, 0.25);
}}
.login-btn {{
  width: 100%;
  padding: 14px;
  background: var(--red);
  border: none;
  border-radius: 12px;
  color: #fff;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-top: 10px;
}}
.login-btn:hover {{
  background: var(--red-dark);
  transform: translateY(-1px);
}}
.login-btn:active {{
  transform: translateY(0);
}}

/* Gestione dei permessi di scrittura visivi */
body.user-is-viewer .song-year svg, 
body.user-is-viewer .radio-date-badge svg {{
  display: none !important;
}}
body.user-is-viewer .song-year, 
body.user-is-viewer .radio-date-badge {{
  cursor: default !important;
  pointer-events: none !important;
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  transform: none !important;
  padding: 0 !important;
}}
</style>
</head>
<body>

<!-- SCHERMATA DI LOGIN (GLASSMORPHISM) -->
<div class="login-overlay" id="login-overlay" style="display:none">
  <div class="login-box">
    <div class="login-logo">📻</div>
    <h2>Radio Charts</h2>
    <p>Inserisci le tue credenziali per accedere</p>
    <div class="login-error" id="login-error" style="display:none"></div>
    <div class="input-wrap">
      <span class="input-icon">👤</span>
      <input type="text" id="login-username" placeholder="Username" onkeydown="if(event.key === 'Enter') performLogin()">
    </div>
    <div class="input-wrap">
      <span class="input-icon">🔒</span>
      <input type="password" id="login-password" placeholder="Password" onkeydown="if(event.key === 'Enter') performLogin()">
    </div>
    <button class="login-btn" id="login-submit-btn" onclick="performLogin()">
      <span class="btn-text">Accedi</span>
      <span class="btn-spinner" style="display:none">Verifica in corso... ⏳</span>
    </button>
  </div>
</div>

<header>
  <div class="header-top">
    <div class="logo">
      <div class="logo-icon">📻</div>
      <div class="logo-text">
        <h1>Radio Charts</h1>
        <span>Classifica Airplay</span>
      </div>
    </div>
    <div class="header-meta">
      Aggiornato il<strong>{today_str}</strong>
    </div>
  </div>
  <div class="radio-tabs">
    <button class="radio-tab active" onclick="switchRadio('subasio')">Radio Subasio</button>
    <button class="radio-tab" onclick="switchRadio('divina')">Radio Divina</button>
    <button class="radio-tab" onclick="switchRadio('mitology')">Radio Mitology</button>
    <button class="radio-tab" onclick="switchRadio('nostalgia')">Nostalgia Toscana</button>
    <button class="radio-tab" onclick="switchRadio('toscana')">Radio Toscana</button>
    <button class="radio-tab" onclick="switchRadio('italia')">Radio Italia</button>
    <button class="radio-tab" onclick="switchRadio('rds')">RDS</button>
    <button class="radio-tab" onclick="switchRadio('rtl1025')">RTL 102.5</button>
    <button class="radio-tab globale" id="tab-globale" onclick="switchRadio('globale')">🌍 Classifica Globale</button>
  </div>
</header>

<div class="global-selector-bar" id="global-selector-bar">
  <span class="global-selector-label">Seleziona radio da sommare:</span>
  <div class="global-checkboxes">
    <label class="global-cb-wrap checked" id="cb-subasio">
      <input type="checkbox" checked onchange="toggleGlobalRadio('subasio')" data-radio="subasio">
      <span class="global-cb-check"></span>
      <span class="global-cb-label">Subasio</span>
    </label>
    <label class="global-cb-wrap checked" id="cb-divina">
      <input type="checkbox" checked onchange="toggleGlobalRadio('divina')" data-radio="divina">
      <span class="global-cb-check"></span>
      <span class="global-cb-label">Divina</span>
    </label>
    <label class="global-cb-wrap checked" id="cb-mitology">
      <input type="checkbox" checked onchange="toggleGlobalRadio('mitology')" data-radio="mitology">
      <span class="global-cb-check"></span>
      <span class="global-cb-label">Mitology</span>
    </label>
    <label class="global-cb-wrap checked" id="cb-nostalgia">
      <input type="checkbox" checked onchange="toggleGlobalRadio('nostalgia')" data-radio="nostalgia">
      <span class="global-cb-check"></span>
      <span class="global-cb-label">Nostalgia</span>
    </label>
    <label class="global-cb-wrap checked" id="cb-toscana">
      <input type="checkbox" checked onchange="toggleGlobalRadio('toscana')" data-radio="toscana">
      <span class="global-cb-check"></span>
      <span class="global-cb-label">Toscana</span>
    </label>
    <label class="global-cb-wrap checked" id="cb-italia">
      <input type="checkbox" checked onchange="toggleGlobalRadio('italia')" data-radio="italia">
      <span class="global-cb-check"></span>
      <span class="global-cb-label">Italia</span>
    </label>
    <label class="global-cb-wrap checked" id="cb-rds">
      <input type="checkbox" checked onchange="toggleGlobalRadio('rds')" data-radio="rds">
      <span class="global-cb-check"></span>
      <span class="global-cb-label">RDS</span>
    </label>
    <label class="global-cb-wrap checked" id="cb-rtl1025">
      <input type="checkbox" checked onchange="toggleGlobalRadio('rtl1025')" data-radio="rtl1025">
      <span class="global-cb-check"></span>
      <span class="global-cb-label">RTL 102.5</span>
    </label>
  </div>
  <div class="global-actions">
    <button class="global-action-btn" onclick="selectAllGlobal()">✓ Tutte</button>
    <button class="global-action-btn" onclick="selectNoneGlobal()">✕ Nessuna</button>
  </div>
</div>

<div class="stats-strip">
  <div class="stat-chip"><div class="val" id="stat-songs">—</div><div class="lbl">Brani</div></div>
  <div class="stat-chip"><div class="val" id="stat-plays">—</div><div class="lbl">Passaggi Totali</div></div>
  <div class="stat-chip"><div class="val" id="stat-days">—</div><div class="lbl">Giorni Monitorati</div></div>
  <div class="stat-chip"><div class="val" id="stat-top" style="font-size:13px">—</div><div class="lbl">Artista #1</div></div>
</div>

<div class="filters-bar">
  <!-- Riga 1: Cerca + Esporta -->
  <div class="filter-row main-filter-row">
    <div class="search-box">
      <input type="text" id="search-input" placeholder="Cerca artista o titolo…" oninput="applyFilters()">
      <span class="icon">🔍</span>
    </div>
    <button class="export-btn" id="export-btn" onclick="exportToCSV()" title="Esporta classifica filtrata in CSV">📥 Esporta CSV</button>
  </div>

  <!-- Riga 2: Decennio Chips -->
  <div class="filter-row chips-filter-row">
    <span class="filter-label">Decennio:</span>
    <div class="decade-chips" id="decade-chips"></div>
  </div>

  <!-- Riga 3: Dropdowns (Data e Orario affiancati) -->
  <div class="filter-row dropdowns-filter-row">
    <div class="filter-select-group">
      <span class="filter-label">Data:</span>
      <div class="date-filter-wrap">
        <button class="date-filter-btn" id="date-filter-btn" onclick="toggleDatePanel()">
          Tutte <span id="date-filter-badge" style="display:none"></span> ▾
        </button>
        <div class="date-panel" id="date-panel">
          <div class="cal-shortcuts">
            <button class="cal-shortcut-btn" id="preset-all"       onclick="selectPreset('all')">Tutte</button>
            <button class="cal-shortcut-btn" id="preset-7"         onclick="selectPreset(7)">Ultimi 7 gg</button>
            <button class="cal-shortcut-btn" id="preset-30"        onclick="selectPreset(30)">Ultimo mese</button>
            <button class="cal-shortcut-btn" id="preset-prevmonth" onclick="selectPreset('prev-month')">Mese scorso</button>
          </div>
          <div class="cal-nav">
            <button class="cal-nav-btn" onclick="calShiftMonth(-1)">&#8249;</button>
            <span class="cal-month-label" id="cal-month-label"></span>
            <button class="cal-nav-btn" onclick="calShiftMonth(1)">&#8250;</button>
          </div>
          <div class="cal-grid" id="cal-grid">
            <div class="cal-head">Lu</div><div class="cal-head">Ma</div>
            <div class="cal-head">Me</div><div class="cal-head">Gi</div>
            <div class="cal-head">Ve</div><div class="cal-head">Sa</div>
            <div class="cal-head">Do</div>
          </div>
        </div>
      </div>
    </div>

    <div class="filter-select-group">
      <span class="filter-label">Orario:</span>
      <div class="hour-filter-wrap">
        <button class="hour-filter-btn" id="hour-filter-btn" onclick="toggleHourPanel()">
          Tutto <span id="hour-filter-badge" style="display:none"></span> ▾
        </button>
        <div class="hour-panel" id="hour-panel">
          <div class="cal-shortcuts">
            <button class="cal-shortcut-btn" id="hour-preset-all"   onclick="selectHourPreset('all')">Tutto</button>
            <button class="cal-shortcut-btn" id="hour-preset-none"  onclick="selectHourPreset('none')">Nessuno</button>
            <button class="cal-shortcut-btn" id="hour-preset-day"   onclick="selectHourPreset('day')">Diurno (07-21)</button>
            <button class="cal-shortcut-btn" id="hour-preset-night" onclick="selectHourPreset('night')">Notturno (21-07)</button>
          </div>
          <div class="hour-grid" id="hour-grid"></div>
        </div>
      </div>
    </div>
  </div>

  <!-- Riga 4: Controlli e picchi (Mostra, Min Passaggi, Posiz. Originale affiancati) -->
  <div class="filter-row controls-filter-row">
    <label class="toggle-wrap" title="Mantieni la posizione originale del brano in classifica anche quando filtri per nome">
      <input type="checkbox" id="keep-rank-checkbox" onchange="applyFilters()">
      <span class="toggle-switch"></span>
      <span>Posiz. Orig.</span>
    </label>
    
    <div class="filter-input-group">
      <span class="filter-label">Mostra:</span>
      <input type="number" class="filter-input" id="top-input" min="1" placeholder="Tutte" oninput="applyFilters()">
    </div>
    
    <div class="filter-input-group">
      <span class="filter-label">Min Passaggi:</span>
      <input type="number" class="filter-input" id="min-plays-input" min="1" placeholder="1" oninput="applyFilters()">
    </div>
    
    <div class="results-count-wrap">
      <span class="results-count" id="results-count"></span>
    </div>
  </div>
</div>

<div class="table-wrap">
  <table>
    <thead>
      <tr>
        <th onclick="sortBy('plays', event)" style="width:52px;cursor:pointer" title="Ordina per posizione / passaggi">#</th>
        <th style="width:38px;cursor:default"></th>
        <th onclick="sortBy('artist', event)" title="Maiusc+Clic per ordinamenti multipli">Artista / Titolo</th>
        <th onclick="sortBy('radioDate', event)" style="text-align:center;width:120px" title="Maiusc+Clic per ordinamenti multipli">Radio Date</th>
        <th class="sorted-desc" onclick="sortBy('plays', event)" style="text-align:center" title="Maiusc+Clic per ordinamenti multipli">Passaggi</th>
        <th class="meta-cell" onclick="sortBy('peak', event)" style="text-align:center" title="Maiusc+Clic per ordinamenti multipli">Picco</th>
        <th class="meta-cell" onclick="sortBy('days', event)" style="text-align:center" title="Maiusc+Clic per ordinamenti multipli">Giorni</th>
      </tr>
    </thead>
    <tbody id="chart-body"></tbody>
  </table>
  <div class="empty-state" id="empty-state" style="display:none">
    <div class="icon">🔍</div>
    <p>Nessun brano trovato per questa ricerca.</p>
  </div>
</div>

<!-- MODAL POPUP -->
<div class="modal-overlay" id="modal-overlay" onclick="closeModal(event)">
  <div class="modal" id="modal-box">
    <div class="modal-header">
      <div class="modal-title">
        <div class="modal-artist" id="modal-artist"></div>
        <div class="modal-song" id="modal-song"></div>
      </div>
      <button class="play-btn play-btn-lg" id="modal-play-btn" title="Ascolta anteprima" onclick="playPreview(currentModalSong.artist,currentModalSong.title,this,currentModalSong.previewUrl)" style="margin-right:8px">▶</button>
      <button class="modal-close" onclick="closeModalDirect()">✕</button>
    </div>
    <div class="modal-tabs">
      <button class="modal-tab-btn active" id="tab-btn-song" onclick="showModalTab('song')">Questo brano</button>
      <button class="modal-tab-btn" id="tab-btn-artist" onclick="showModalTab('artist')">Artista <span id="tab-artist-count"></span></button>
    </div>
    <div class="modal-body">
      <div class="modal-tab-pane active" id="tab-pane-song"></div>
      <div class="modal-tab-pane" id="tab-pane-artist"></div>
    </div>
  </div>
</div>

<!-- EDIT OVERRIDES MODAL -->
<div class="modal-overlay" id="edit-year-modal-overlay" onclick="closeEditYearModal(event)">
  <div class="modal edit-modal" id="edit-year-modal-box">
    <div class="modal-header">
      <div class="modal-title">
        <div class="edit-modal-title-text">Modifica Dati Brano</div>
        <div class="edit-modal-subtitle" id="edit-year-subtitle">
          <span id="edit-year-artist" class="bold-text"></span> &middot; <span id="edit-year-title" class="bold-text"></span>
        </div>
      </div>
      <button class="modal-close" onclick="closeEditYearModalDirect()">✕</button>
    </div>
    <div class="modal-body edit-modal-body">
      <!-- Error Banner -->
      <div class="edit-error-banner" id="edit-year-error" style="display:none"></div>
      
      <!-- Success Banner -->
      <div class="edit-success-banner" id="edit-year-success" style="display:none">
        <div class="checkmark-wrapper">
          <svg class="checkmark" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 52">
            <circle class="checkmark__circle" cx="26" cy="26" r="25" fill="none"/>
            <path class="checkmark__check" fill="none" d="M14.1 27.2l7.1 7.2 16.7-16.8"/>
          </svg>
        </div>
        <span>Dati aggiornati con successo!</span>
      </div>

      <div class="edit-form-content" id="edit-year-form-content">
        <button class="edit-btn edit-btn-search" id="edit-year-search-online-btn" onclick="searchSongDataOnline()">
          <span class="btn-search-text">🔍 Trova anno e radio date online</span>
          <span class="btn-search-spinner" style="display:none">Ricerca in corso... ⏳</span>
        </button>
        
        <label for="edit-year-input" class="edit-input-label">Anno di Pubblicazione</label>
        <div class="input-with-icon" style="margin-bottom: 16px;">
          <span class="input-icon">📅</span>
          <input type="number" id="edit-year-input" min="1900" max="2100" placeholder="e.g. 1995" class="edit-year-input-field" onkeydown="if(event.key === 'Enter') saveYearOverride()">
        </div>

        <label for="edit-radiodate-input" class="edit-input-label">Radio Date (GG/MM/AAAA)</label>
        <div class="input-with-icon" style="margin-bottom: 24px;">
          <span class="input-icon">⏱</span>
          <input type="text" id="edit-radiodate-input" placeholder="e.g. 15/05/2026" class="edit-year-input-field" onkeydown="if(event.key === 'Enter') saveYearOverride()">
        </div>
        
        <div class="edit-modal-actions">
          <button class="edit-btn edit-btn-cancel" id="edit-btn-cancel" onclick="closeEditYearModalDirect()">Annulla</button>
          <button class="edit-btn edit-btn-save" id="edit-year-save-btn" onclick="saveYearOverride()">
            <span class="btn-text">Salva</span>
            <span class="btn-spinner" style="display:none">Salvataggio... ⏳</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</div>

<script>
const APPS_SCRIPT_URL = "{APPS_SCRIPT_URL}";
const RAW = {{
  subasio:{json_subasio},
  divina:{json_divina},
  mitology:{json_mitology},
  nostalgia:{json_nostalgia},
  toscana:{json_toscana},
  italia:{json_italia},
  rds:{json_rds},
  rtl1025:{json_rtl1025}
}};

let currentRadio = 'subasio';
let allSongs = [];
let allDates = [];
let selectedDates = null;  // null = tutte le date; Set = date selezionate
let currentSort = [{{col:'plays', dir:'desc'}}];
let activeDecade = 'all';

const RADIO_KEYS = ['subasio','divina','mitology','nostalgia','toscana','italia','rds','rtl1025'];
const RADIO_LABELS = {{
  subasio: 'Radio Subasio', divina: 'Radio Divina', mitology: 'Radio Mitology',
  nostalgia: 'Nostalgia Toscana', toscana: 'Radio Toscana', italia: 'Radio Italia',
  rds: 'RDS', rtl1025: 'RTL 102.5'
}};
let globalSelectedRadios = new Set(RADIO_KEYS);
let isGlobale = false;
let lastFilteredSongs = [];

function getNormKey(artist, title) {{
  let a = (artist||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').trim();
  let t = (title||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').trim();
  
  a = a.replace(/\s*\(\d{{4}}\)\s*$/g, '').replace(/\s*\(\d{{4}}\)/g, '');
  t = t.replace(/\s*\(\d{{4}}\)\s*$/g, '').replace(/\s*\(\d{{4}}\)/g, '');
  
  // Standardize MC spacing (e.g. "Mc Cartney" -> "McCartney")
  a = a.replace(/\bmc\s+/gi, 'mc');
  // Standardize All Stars spacing
  a = a.replace(/\ball\s*stars?\b/gi, 'allstars');
  // Strip dots first to handle acronyms (e.g. R.E.O. -> REO, U.B.40 -> UB40) before splitting
  a = a.replace(/\./g, '');
  
  // Estrae artisti secondari dal titolo se presenti
  let titleClean = t;
  const featPattern = /\b(feat|ft|featuring|with)\b\.?\s*(.*?)(?:\)|$)/i;
  const featMatch = titleClean.match(featPattern);
  if (featMatch) {{
    const addArt = featMatch[2].toLowerCase();
    const artPartClean = a.toLowerCase().replace(/[^a-z0-9]/g,'');
    const addArtClean = addArt.replace(/[^a-z0-9]/g,'');
    if (addArtClean && !artPartClean.includes(addArtClean)) {{
      a += " , " + featMatch[2];
    }}
    titleClean = titleClean.replace(featPattern, '');
  }}
  
  // Rimuove parentesi che contengono parole chiave di versioni/remix
  const versionRegex = /\(\s*.*?\b(radio|edit|version|remix|rmx|mix|live|acoustic|instrumental|extended|single|album|cover|tribute|original|mono|stereo|remastered|remaster)\b.*?\)/gi;
  titleClean = titleClean.replace(versionRegex, '');
  
  // Rimuove separatori seguiti da parole chiave di versioni alla fine del titolo
  const endVersionRegex = /\s*[\-–—,/]\s*.*?\b(radio|edit|version|remix|rmx|mix|live|acoustic|instrumental|extended|single|album|cover|tribute|original|mono|stereo|remastered|remaster)\b.*?$/gi;
  titleClean = titleClean.replace(endVersionRegex, '');
  
  // Rimuove eventuali parentesi rimanenti lasciando il contenuto
  titleClean = titleClean.replace(/[()]/g, ' ').replace(/\s+/g, ' ').trim();
  
  // Normalizza gli artisti
  const parts = a.split(/\bfeat\.?\b|\bft\.?\b|\bfeaturing\b|&|\be\b|\band\b|,|\/|\+/i);
  const cleaned = [];
  parts.forEach(p => {{
    const pClean = p.replace(/\./g, '');
    const words = pClean.split(/[\s\-_]+/);
    const cleanedWords = [];
    words.forEach(w => {{
      const wClean = w.replace(/[^a-z0-9]/g,'');
      if (wClean && wClean !== 'the' && wClean !== 'band' && wClean !== 'group') {{
        cleanedWords.push(wClean);
      }}
    }});
    cleanedWords.sort();
    const artClean = cleanedWords.join('');
    if (artClean && !cleaned.includes(artClean)) {{
      cleaned.push(artClean);
    }}
  }});
  
  cleaned.sort();
  const canonicalArtist = cleaned.join('');
  const canonicalTitle = titleClean.replace(/[^a-z0-9]/g,'');
  
  return canonicalArtist ? (canonicalArtist + '|' + canonicalTitle) : canonicalTitle;
}}

function buildGlobalData() {{
  let mergedSongs = {{}};
  let allDatesSet = new Set();
  
  RADIO_KEYS.forEach(radioKey => {{
    if (!globalSelectedRadios.has(radioKey)) return;
    const src = RAW[radioKey];
    if (src && src.dates) {{
      src.dates.forEach(d => allDatesSet.add(d));
    }}
  }});
  
  allDates = Array.from(allDatesSet).sort((a, b) => {{
    const [da, ma, ya] = a.split('/').map(Number);
    const [db, mb, yb] = b.split('/').map(Number);
    return new Date(ya, ma - 1, da) - new Date(yb, mb - 1, db);
  }});
  
  RADIO_KEYS.forEach(radioKey => {{
    if (!globalSelectedRadios.has(radioKey)) return;
    const src = RAW[radioKey];
    if (!src || !src.songs) return;
    
    src.songs.forEach(song => {{
      const key = getNormKey(song.artist, song.title);
      if (!mergedSongs[key]) {{
        mergedSongs[key] = {{
          artist: song.artist,
          title: song.title,
          year: song.year || 'N/A',
          radioDate: song.radioDate || 'N/D',
          total: 0,
          days: {{}},
          peak: 999,
          daysCount: 0,
          sourceRadios: new Set()
        }};
      }}
      
      const s = mergedSongs[key];
      s.total += song.total;
      s.sourceRadios.add(radioKey);
      
      if (song.year && song.year !== 'N/A' && (s.year === 'N/A' || s.year === '')) {{
        s.year = song.year;
      }}
      if (song.radioDate && song.radioDate !== 'N/A' && song.radioDate !== 'N/D' && (s.radioDate === 'N/D' || s.radioDate === 'N/A')) {{
        s.radioDate = song.radioDate;
      }}
      
      Object.keys(song.days).forEach(dateStr => {{
        if (!s.days[dateStr]) {{
          s.days[dateStr] = [];
        }}
        const times = song.days[dateStr];
        times.forEach(tStr => {{
          const cleanTime = tStr.split(' ')[0];
          s.days[dateStr].push(`${{cleanTime}} [${{radioKey}}]`);
        }});
      }});
      
      if (song.rank && song.rank < s.peak) {{
        s.peak = song.rank;
      }}
    }});
  }});
  
  allSongs = Object.values(mergedSongs);
  
  allSongs = allSongs.map(s => {{
    s.daysCount = Object.keys(s.days).length;
    Object.keys(s.days).forEach(d => {{
      s.days[d].sort((a,b) => a.localeCompare(b));
    }});
    return s;
  }});
  
  allSongs.sort((a, b) => b.total - a.total);
  
  allSongs.forEach((s, idx) => {{
    s.rank = idx + 1;
    s.peak = s.peak === 999 ? s.rank : s.peak;
  }});
}}

function switchRadio(radio) {{
  currentRadio = radio;
  isGlobale = (radio === 'globale');
  
  const selectorBar = document.getElementById('global-selector-bar');
  if (isGlobale) {{
    selectorBar.classList.add('show');
  }} else {{
    selectorBar.classList.remove('show');
  }}
  
  document.querySelectorAll('.radio-tab').forEach(t => {{
    if (radio === 'globale') {{
      t.classList.toggle('active', t.id === 'tab-globale');
    }} else {{
      t.classList.toggle('active', !t.id && t.getAttribute('onclick').includes(`'${{radio}}'`));
    }}
  }});
  
  if (isGlobale) {{
    buildGlobalData();
    selectedDates = null;
    activeDecade = 'all';
    document.getElementById('date-panel').classList.remove('open');
    loadData();
    return;
  }}
  
  const src = RAW[currentRadio];
  
  if (selectedDates) {{
    const newDatesSet = new Set(src.dates);
    const validSelected = new Set([...selectedDates].filter(d => newDatesSet.has(d)));
    if (validSelected.size === 0) {{
      selectedDates = null;
    }} else {{
      selectedDates = validSelected;
    }}
  }}
  
  if (activeDecade !== 'all') {{
    const hasDecade = src.songs.some(s => s.year && Math.floor(parseInt(s.year)/10)*10 === activeDecade);
    if (!hasDecade) {{
      activeDecade = 'all';
    }}
  }}
  
  document.getElementById('date-panel').classList.remove('open');
  loadData();
}}

function loadData() {{
  if (!isGlobale) {{
    const src = RAW[currentRadio];
    allDates = src.dates;

    allSongs = src.songs.map((s, idx) => {{
      s.daysCount = Object.keys(s.days).length;
      s.peak = s.rank;
      return s;
    }});
  }}

  const totalPlays = allSongs.reduce((a,s) => a+s.total, 0);
  document.getElementById('stat-songs').textContent = allSongs.length;
  document.getElementById('stat-plays').textContent = totalPlays.toLocaleString('it-IT');
  document.getElementById('stat-days').textContent = allDates.length;
  document.getElementById('stat-top').textContent = allSongs[0]?.artist || '—';

  buildDecadeChips();
  buildDatePanel();
  buildHourPanel();
  applyFilters();
}}

function toggleGlobalRadio(radioKey) {{
  const wrap = document.getElementById(`cb-${{radioKey}}`);
  const checkbox = wrap.querySelector('input[type="checkbox"]');
  
  if (checkbox.checked) {{
    globalSelectedRadios.add(radioKey);
    wrap.classList.add('checked');
  }} else {{
    globalSelectedRadios.delete(radioKey);
    wrap.classList.remove('checked');
  }}
  
  buildGlobalData();
  loadData();
}}

function selectAllGlobal() {{
  RADIO_KEYS.forEach(radioKey => {{
    globalSelectedRadios.add(radioKey);
    const wrap = document.getElementById(`cb-${{radioKey}}`);
    wrap.classList.add('checked');
    wrap.querySelector('input[type="checkbox"]').checked = true;
  }});
  buildGlobalData();
  loadData();
}}

function selectNoneGlobal() {{
  globalSelectedRadios.clear();
  RADIO_KEYS.forEach(radioKey => {{
    const wrap = document.getElementById(`cb-${{radioKey}}`);
    wrap.classList.remove('checked');
    wrap.querySelector('input[type="checkbox"]').checked = false;
  }});
  buildGlobalData();
  loadData();
}}

function exportToCSV() {{
  if (!lastFilteredSongs || lastFilteredSongs.length === 0) {{
    alert("Nessun dato da esportare con i filtri attuali!");
    return;
  }}
  
  const headers = ["Posizione", "Artista", "Titolo", "Anno", "Radio Date", "Passaggi", "Picco", "Giorni"];
  
  const rows = lastFilteredSongs.map((s, idx) => {{
    const pos = document.getElementById('keep-rank-checkbox').checked ? s.rank : (idx + 1);
    const plays = s._filtTotal !== undefined ? s._filtTotal : s.total;
    
    const cleanField = (f) => {{
      const str = String(f || '').replace(/"/g, '""');
      return `"${{str}}"`;
    }};
    
    return [
      pos,
      cleanField(s.artist),
      cleanField(s.title),
      cleanField(s.year),
      cleanField(s.radioDate),
      plays,
      s.peak,
      s.daysCount
    ].join(',');
  }});
  
  const csvContent = "\\ufeff" + [headers.join(','), ...rows].join('\\n');
  const blob = new Blob([csvContent], {{ type: 'text/csv;charset=utf-8;' }});
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  
  const radioName = isGlobale ? 'Classifica_Globale' : RADIO_LABELS[currentRadio].replace(/\s+/g, '_');
  const filename = `${{radioName}}_Report_${{new Date().toISOString().slice(0,10)}}.csv`;
  
  link.setAttribute("href", url);
  link.setAttribute("download", filename);
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}}

function buildDecadeChips() {{
  const decades = new Set(['all']);
  allSongs.forEach(s => {{
    if(s.year && s.year !== 'N/A') {{
      decades.add(Math.floor(parseInt(s.year)/10)*10);
    }}
  }});
  const sortedDecades = ['all', ...[...decades].filter(d=>d!=='all').sort((a,b)=>b-a)];
  const container = document.getElementById('decade-chips');
  container.innerHTML = sortedDecades.map(d => {{
    const label = d === 'all' ? 'Tutti' : `${{d}}s`;
    return `<span class="chip${{activeDecade==d?' active':''}}" onclick="filterDecade(${{JSON.stringify(d)}})">${{label}}</span>`;
  }}).join('');
}}

function filterDecade(d) {{
  activeDecade = d;
  applyFilters();
  buildDecadeChips();
}}

// ── CALENDARIO DATE ───────────────────────────────────────────────────────────
let calYear, calMonth;
let allDatesSet = new Set();

// Converte "DD.MM" → Date JS (inferisce l'anno: se la data risulta >7gg nel futuro → anno scorso)
function ddmmToDate(ddmm) {{
  const [dd, mm] = ddmm.split('.').map(Number);
  const now = new Date(); now.setHours(0,0,0,0);
  let yr = now.getFullYear();
  let d = new Date(yr, mm-1, dd);
  if (d - now > 7 * 86400000) yr--;
  return new Date(yr, mm-1, dd);
}}

let selectedHours = null; // null = all hours active

function toggleHourPanel() {{
  document.getElementById('hour-panel').classList.toggle('open');
}}

function buildHourPanel() {{
  const grid = document.getElementById('hour-grid');
  if (!grid) return;
  
  // Evita di rigenerare se gia popolato
  if (grid.childElementCount > 0) {{
    updateHourUI();
    return;
  }}
  
  grid.innerHTML = '';
  for (let h = 0; h < 24; h++) {{
    const hStr = h.toString().padStart(2, '0');
    
    // Contenitore
    const label = document.createElement('label');
    label.className = 'hour-cb-wrap active';
    label.id = `hour-cb-wrap-${{h}}`;
    
    // Checkbox
    const cb = document.createElement('input');
    cb.type = 'checkbox';
    cb.checked = true;
    cb.id = `hour-cb-${{h}}`;
    cb.onchange = () => toggleHour(h);
    
    // Label text
    const text = document.createElement('span');
    text.textContent = hStr;
    
    label.appendChild(cb);
    label.appendChild(text);
    grid.appendChild(label);
  }}
  updateHourBadge();
}}

function toggleHour(h) {{
  if (!selectedHours) {{
    selectedHours = new Set();
    for (let i = 0; i < 24; i++) {{
      if (i !== h) selectedHours.add(i);
    }}
  }} else {{
    if (selectedHours.has(h)) {{
      selectedHours.delete(h);
    }} else {{
      selectedHours.add(h);
    }}
    if (selectedHours.size === 24) {{
      selectedHours = null;
    }}
  }}
  updateHourUI();
  applyFilters();
}}

function updateHourUI() {{
  for (let h = 0; h < 24; h++) {{
    const label = document.getElementById(`hour-cb-wrap-${{h}}`);
    const cb = document.getElementById(`hour-cb-${{h}}`);
    if (label && cb) {{
      const isActive = !selectedHours || selectedHours.has(h);
      cb.checked = isActive;
      if (isActive) {{
        label.classList.add('active');
      }} else {{
        label.classList.remove('active');
      }}
    }}
  }}
  updateHourBadge();
}}

function updateHourBadge() {{
  const badge = document.getElementById('hour-filter-badge');
  const btn = document.getElementById('hour-filter-btn');
  if (!btn) return;
  
  if (!selectedHours || selectedHours.size === 24) {{
    btn.firstChild.textContent = 'Tutto ';
    if (badge) badge.style.display = 'none';
    btn.classList.remove('active');
  }} else if (selectedHours.size === 0) {{
    btn.firstChild.textContent = 'Nessuno ';
    if (badge) badge.style.display = 'none';
    btn.classList.add('active');
  }} else {{
    btn.firstChild.textContent = 'Personalizzato ';
    if (badge) {{
      badge.textContent = `${{selectedHours.size}} h`;
      badge.style.display = 'inline-block';
    }}
    btn.classList.add('active');
  }}
}}

function selectHourPreset(preset) {{
  if (preset === 'all') {{
    selectedHours = null;
  }} else if (preset === 'none') {{
    selectedHours = new Set();
  }} else if (preset === 'day') {{
    selectedHours = new Set();
    for (let h = 7; h <= 20; h++) selectedHours.add(h);
  }} else if (preset === 'night') {{
    selectedHours = new Set();
    for (let h = 21; h < 24; h++) selectedHours.add(h);
    for (let h = 0; h <= 6; h++) selectedHours.add(h);
  }}
  updateHourUI();
  applyFilters();
}}

function toggleDatePanel() {{
  document.getElementById('date-panel').classList.toggle('open');
}}

function buildDatePanel() {{
  allDatesSet = new Set(allDates);
  const now = new Date(); now.setHours(0,0,0,0);
  // Mostra il mese più recente tra le date disponibili
  if (allDates.length) {{
    const latest = allDates.reduce((a,b) => ddmmToDate(a) > ddmmToDate(b) ? a : b);
    const ld = ddmmToDate(latest);
    calYear = ld.getFullYear(); calMonth = ld.getMonth();
  }} else {{
    calYear = now.getFullYear(); calMonth = now.getMonth();
  }}
  buildCalendar();
  updateDateBadge();
}}

function buildCalendar() {{
  const MONTHS = ['Gennaio','Febbraio','Marzo','Aprile','Maggio','Giugno',
                  'Luglio','Agosto','Settembre','Ottobre','Novembre','Dicembre'];
  document.getElementById('cal-month-label').textContent = MONTHS[calMonth] + ' ' + calYear;
  const grid = document.getElementById('cal-grid');
  const daysInMonth = new Date(calYear, calMonth+1, 0).getDate();
  let dow = new Date(calYear, calMonth, 1).getDay(); // 0=dom
  dow = dow === 0 ? 6 : dow - 1; // converti a lun=0
  let html = '';
  for (let i=0; i<dow; i++) html += '<div class="cal-cell empty"></div>';
  for (let day=1; day<=daysInMonth; day++) {{
    const mm = String(calMonth+1).padStart(2,'0');
    const dd = String(day).padStart(2,'0');
    const key = dd + '.' + mm;
    const hasData = allDatesSet.has(key);
    const isSel = !selectedDates || selectedDates.has(key);
    let cls = 'cal-cell';
    if (hasData) {{ cls += ' has-data'; if (isSel) cls += ' selected'; }}
    else cls += ' no-data';
    const click = hasData ? ` onclick="onCalDayClick('${{key}}')"` : '';
    html += `<div class="${{cls}}"${{click}}>${{day}}</div>`;
  }}
  // Aggiungi celle vuote di fine riga per completare la griglia
  const total = dow + daysInMonth;
  const rem = total % 7;
  if (rem) for (let i=0; i<7-rem; i++) html += '<div class="cal-cell empty"></div>';
  // Rimuovi vecchie celle (lascia le intestazioni)
  const existing = grid.querySelectorAll('.cal-cell');
  existing.forEach(c => c.remove());
  grid.insertAdjacentHTML('beforeend', html);
  updatePresetButtons();
}}

function calShiftMonth(delta) {{
  calMonth += delta;
  if (calMonth > 11) {{ calMonth = 0; calYear++; }}
  if (calMonth < 0)  {{ calMonth = 11; calYear--; }}
  buildCalendar();
}}

function onCalDayClick(ddmm) {{
  if (!selectedDates) {{
    // Era "tutte" → seleziona solo questo giorno
    selectedDates = new Set([ddmm]);
  }} else {{
    if (selectedDates.has(ddmm)) selectedDates.delete(ddmm);
    else selectedDates.add(ddmm);
    // Se sono di nuovo tutte → torna a null
    const dataKeys = [...allDatesSet];
    if (dataKeys.every(k => selectedDates.has(k))) selectedDates = null;
  }}
  updateDateBadge();
  applyFilters();
  buildCalendar();
}}

function selectPreset(type) {{
  const now = new Date(); now.setHours(0,0,0,0);
  if (type === 'all') {{
    selectedDates = null;
  }} else if (typeof type === 'number') {{
    const cutoff = new Date(now.getTime() - (type-1)*86400000);
    const sel = allDates.filter(d => {{ const dt = ddmmToDate(d); return dt >= cutoff && dt <= now; }});
    selectedDates = sel.length === allDates.length ? null : new Set(sel);
    // Naviga al mese di inizio selezione
    if (sel.length) {{ const d = ddmmToDate(sel[sel.length-1]); calYear=d.getFullYear(); calMonth=d.getMonth(); }}
  }} else if (type === 'prev-month') {{
    let pm = now.getMonth() - 1, py = now.getFullYear();
    if (pm < 0) {{ pm = 11; py--; }}
    const sel = allDates.filter(d => {{ const dt = ddmmToDate(d); return dt.getMonth()===pm && dt.getFullYear()===py; }});
    selectedDates = sel.length === allDates.length ? null : new Set(sel);
    calYear = py; calMonth = pm;
  }}
  updateDateBadge();
  applyFilters();
  buildCalendar();
}}

function updateDateBadge() {{
  const btn = document.getElementById('date-filter-btn');
  if (!selectedDates) {{
    btn.classList.remove('active');
    btn.innerHTML = 'Tutte ▾';
  }} else {{
    const n = selectedDates.size;
    btn.classList.toggle('active', n > 0);
    btn.innerHTML = (n===0 ? 'Nessuna' : n + (n===1?' giorno':' giorni')) + ' ▾';
  }}
}}

function updatePresetButtons() {{
  // Evidenzia il preset attivo (se coincide)
  const now = new Date(); now.setHours(0,0,0,0);
  const check = (type) => {{
    if (type==='all') return !selectedDates;
    if (!selectedDates) return false;
    if (typeof type==='number') {{
      const cutoff = new Date(now.getTime() - (type-1)*86400000);
      const expected = new Set(allDates.filter(d => {{ const dt=ddmmToDate(d); return dt>=cutoff&&dt<=now; }}));
      return expected.size===selectedDates.size && [...expected].every(k=>selectedDates.has(k));
    }}
    if (type==='prev-month') {{
      let pm=now.getMonth()-1, py=now.getFullYear(); if(pm<0){{pm=11;py--;}}
      const expected = new Set(allDates.filter(d=>{{ const dt=ddmmToDate(d); return dt.getMonth()===pm&&dt.getFullYear()===py; }}));
      return expected.size===selectedDates.size && [...expected].every(k=>selectedDates.has(k));
    }}
    return false;
  }};
  [['all','preset-all'],[7,'preset-7'],[30,'preset-30'],['prev-month','preset-prevmonth']].forEach(([t,id])=>{{
    const el = document.getElementById(id);
    if(el) el.classList.toggle('active', check(t));
  }});
}}

// Chiudi panel cliccando fuori
document.addEventListener('click', e => {{
  const wrap = document.getElementById('date-filter-btn')?.closest('.date-filter-wrap');
  if(wrap && !wrap.contains(e.target)) {{
    document.getElementById('date-panel').classList.remove('open');
  }}
  const wrapHour = document.getElementById('hour-filter-btn')?.closest('.hour-filter-wrap');
  if(wrapHour && !wrapHour.contains(e.target)) {{
    document.getElementById('hour-panel').classList.remove('open');
  }}
}});

function applyFilters() {{
  const q = document.getElementById('search-input').value.toLowerCase().trim();
  
  const topVal = document.getElementById('top-input').value.trim();
  const topN = (topVal && parseInt(topVal) > 0) ? parseInt(topVal) : 99999;
  
  const minPlaysVal = document.getElementById('min-plays-input').value.trim();
  const minPlays = (minPlaysVal && parseInt(minPlaysVal) > 0) ? parseInt(minPlaysVal) : 1;

  // Calcola totale per le date e orari selezionati
  const getTotal = s => {{
    if (!selectedDates && !selectedHours) return s.total;
    let t = 0;
    const datesToLoop = selectedDates ? selectedDates : Object.keys(s.days);
    datesToLoop.forEach(d => {{
      const playsList = s.days[d];
      if (playsList) {{
        if (!selectedHours) {{
          t += playsList.length;
        }} else {{
          playsList.forEach(timeStr => {{
            const hour = parseInt(timeStr.split(':')[0]);
            if (selectedHours.has(hour)) {{
              t += 1;
            }}
          }});
        }}
      }}
    }});
    return t;
  }};

  // 1. Calcola i totali del periodo per tutti i brani
  let periodRanked = allSongs.map(s => ({{ ...s, _filtTotal: getTotal(s) }}));

  // 2. Ordina per passaggi nel periodo (desc) e usa rank originale come tie-breaker
  periodRanked.sort((a,b) => {{
    const ta = a._filtTotal, tb = b._filtTotal;
    if (ta !== tb) return tb - ta;
    return a.rank - b.rank;
  }});

  // 3. Assegna il rank del periodo
  periodRanked.forEach((s, idx) => {{
    s._periodRank = idx + 1;
  }});

  // 4. Filtra i brani per ricerca e decennio
  let filtered = periodRanked.filter(s => {{
    if((selectedDates || selectedHours) && s._filtTotal === 0) return false;
    if(s._filtTotal < minPlays) return false;
    if(q && !`${{s.artist}} ${{s.title}}`.toLowerCase().includes(q)) return false;
    if(activeDecade !== 'all') {{
      const yr = parseInt(s.year);
      if(isNaN(yr) || Math.floor(yr/10)*10 !== activeDecade) return false;
    }}
    return true;
  }});

  // Sort
  filtered.sort((a,b) => {{
    const ta = a._filtTotal ?? a.total, tb = b._filtTotal ?? b.total;
    for (let i = 0; i < currentSort.length; i++) {{
      const s = currentSort[i];
      const col = s.col;
      const dir = s.dir === 'desc' ? -1 : 1;
      let cmp = 0;
      if(col==='artist') {{
        cmp = a.artist.localeCompare(b.artist);
        if (cmp === 0 && i === currentSort.length - 1) {{
          cmp = a.title.localeCompare(b.title);
        }}
      }}
      else if(col==='plays')  {{ cmp = ta - tb; }}
      else if(col==='peak')   {{ cmp = b.peak - a.peak; }}
      else if(col==='days')   {{ cmp = a.daysCount - b.daysCount; }}
      else if(col==='radioDate') {{
        const getRDVal = (x) => {{
          const rd = x.radioDate;
          if (!rd || rd === 'N/A' || rd === 'N/D') {{
            return dir === -1 ? -9999999999999 : 9999999999999;
          }}
          const parts = rd.split('/');
          if (parts.length === 3) {{
            const d = parseInt(parts[0]), m = parseInt(parts[1]), y = parseInt(parts[2]);
            return new Date(y, m - 1, d).getTime();
          }}
          return dir === -1 ? -9999999999999 : 9999999999999;
        }};
        cmp = getRDVal(a) - getRDVal(b);
      }}
      if (cmp !== 0) return dir * cmp;
    }}
    return a.title.localeCompare(b.title);
  }});

  lastFilteredSongs = filtered;
  const shown = filtered.slice(0, topN);
  document.getElementById('results-count').textContent = `${{shown.length}} / ${{filtered.length}} brani`;
  renderTable(shown);
}}

function sortBy(col, event) {{
  const isMulti = event && event.shiftKey;
  let existingIndex = currentSort.findIndex(s => s.col === col);
  if (isMulti) {{
    if (existingIndex >= 0) {{
      currentSort[existingIndex].dir = currentSort[existingIndex].dir === 'desc' ? 'asc' : 'desc';
    }} else {{
      currentSort.push({{col: col, dir: 'desc'}});
    }}
  }} else {{
    let dir = 'desc';
    if (existingIndex === 0 && currentSort.length === 1) {{
      dir = currentSort[0].dir === 'desc' ? 'asc' : 'desc';
    }}
    currentSort = [{{col: col, dir: dir}}];
  }}

  document.querySelectorAll('thead th').forEach(th => {{
    th.classList.remove('sorted-asc','sorted-desc','sorted-multi');
    th.removeAttribute('data-sort-index');
    const onclickStr = th.getAttribute('onclick') || '';
    const match = onclickStr.match(/sortBy\('([^']+)'/);
    if (match) {{
      const colName = match[1];
      const sortIndex = currentSort.findIndex(s => s.col === colName);
      if (sortIndex >= 0) {{
        const sortObj = currentSort[sortIndex];
        th.classList.add(`sorted-${{sortObj.dir}}`);
        if (currentSort.length > 1) {{
          th.setAttribute('data-sort-index', (sortIndex + 1).toString());
          th.classList.add('sorted-multi');
        }}
      }}
    }}
  }});
  applyFilters();
}}

let renderedSongs = [];  // mappa indice riga → oggetto canzone

function renderTable(songs) {{
  const tbody = document.getElementById('chart-body');
  const empty = document.getElementById('empty-state');

  if(!songs.length) {{
    tbody.innerHTML = '';
    empty.style.display = '';
    renderedSongs = [];
    return;
  }}
  empty.style.display = 'none';
  renderedSongs = songs;  // salva riferimento per showPopup

  const keepRank = document.getElementById('keep-rank-checkbox') && document.getElementById('keep-rank-checkbox').checked;

  tbody.innerHTML = songs.map((s, i) => {{
    const pos = keepRank ? s._periodRank : (i + 1);
    const posClass = pos===1?'pos-1':pos===2?'pos-2':pos===3?'pos-3':pos<=10?'pos-top10':'pos-rest';
    const rowClass = pos===1?'top1':pos===2?'top2':pos===3?'top3':'';

    // Trend rispetto al rank originale del periodo
    const origRank = s._periodRank;
    let trendHtml;
    if(origRank !== (i + 1)) {{
      const diff = origRank - (i + 1);
      trendHtml = diff > 0
        ? `<span class="trend trend-up">▲${{diff}}</span>`
        : `<span class="trend trend-down">▼${{Math.abs(diff)}}</span>`;
    }} else {{
      trendHtml = `<span class="trend trend-stable">—</span>`;
    }}

    const isNa = s.year === 'N/A';
    const displayYear = isNa ? 'N/D' : s.year;
    const yearClass = isNa ? 'song-year na' : 'song-year';
    const yearBadge = `<span class="${{yearClass}}" title="Modifica anno di pubblicazione" onclick="openEditYearModal(event, ${{i}})">${{displayYear}}<svg viewBox="0 0 24 24" style="width:10px;height:10px;margin-left:4px;fill:currentColor;vertical-align:middle"><path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/></svg></span>`;

    const isRdNa = !s.radioDate || s.radioDate === 'N/A' || s.radioDate === 'N/D';
    const displayRd = isRdNa ? 'N/D' : s.radioDate;
    const rdClass = isRdNa ? 'radio-date-badge na' : 'radio-date-badge';
    const radioDateBadge = `<span class="${{rdClass}}" title="Modifica radio date" onclick="openEditYearModal(event, ${{i}})">⏱ ${{displayRd}}<svg viewBox="0 0 24 24" style="width:10px;height:10px;margin-left:4px;fill:currentColor;vertical-align:middle"><path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/></svg></span>`;

    return `<tr class="${{rowClass}}">
      <td class="pos-cell"><div class="pos-badge ${{posClass}}">${{pos}}</div></td>
      <td class="trend-cell">${{trendHtml}}</td>
      <td>
        <div class="song-artist" style="display:flex;align-items:center;gap:6px">
          <span>${{esc(s.artist)}}${{yearBadge}}</span>
          <button class="play-btn" title="Ascolta anteprima" onclick="event.stopPropagation();playPreview(renderedSongs[${{i}}].artist,renderedSongs[${{i}}].title,this,renderedSongs[${{i}}].previewUrl)">▶</button>
        </div>
        <div class="song-title">${{esc(s.title)}}</div>
      </td>
      <td class="radio-date-cell">${{radioDateBadge}}</td>
      <td class="plays-cell" onclick="showPopup(${{i}})" title="Clicca per vedere orari di messa in onda">
        <div class="plays-num">${{s._filtTotal ?? s.total}}</div>
        <div class="plays-lbl">${{selectedDates ? 'nei giorni sel.' : 'pass.'}}</div>
      </td>
      <td class="meta-cell" style="text-align:center">
        <div class="meta-val">#${{s.peak}}</div>
        <div class="meta-lbl">picco</div>
      </td>
      <td class="meta-cell" style="text-align:center">
        <div class="meta-val">${{s.daysCount}}</div>
        <div class="meta-lbl">giorni</div>
      </td>
    </tr>`;
  }}).join('');
}}

function esc(s){{ return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }}

// ── POPUP ────────────────────────────────────────────────────────────────────
function dateToNum(d) {{
  const p = d.split('.');
  const day=parseInt(p[0]), mon=parseInt(p[1]);
  const yr = mon>=10 ? 2025 : 2026;
  return yr*10000 + mon*100 + day;
}}

function buildDayBlocks(days) {{
  const sortedDates = Object.keys(days).sort((a,b) => dateToNum(b) - dateToNum(a));
  let html = '';
  sortedDates.forEach(date => {{
    const times = days[date];
    if(!times || !times.length) return;
    const sortedTimes = [...times].sort();
    html += `<div class="day-block">
      <div class="day-header">
        <span class="day-date">📅 ${{date}}</span>
        <span class="day-count">${{times.length}} passaggio/i</span>
      </div>
      <div class="times-list">
        ${{sortedTimes.filter(t => t !== 'In diretta').map(t => {{
          const parts = t.split(' [');
          const timeVal = parts[0];
          const radioTag = parts.length > 1 ? `<span class="radio-source-tag">${{parts[1].slice(0, -1)}}</span>` : '';
          return `<span class="time-chip">${{esc(timeVal)}}${{radioTag}}</span>`;
        }}).join('')}}
      </div>
    </div>`;
  }});
  return html;
}}

let currentModalSong = {{artist:'', title:''}};

function showPopup(i) {{
  const s = renderedSongs[i];
  if(!s) return;

  // Aggiorna riferimento per il pulsante play del modal
  currentModalSong = s;
  const mPlayBtn = document.getElementById('modal-play-btn');
  if(mPlayBtn) {{
    // Se stava suonando questo brano, mantieni lo stato; altrimenti reset
    if(currentPlayBtn !== mPlayBtn) {{
      mPlayBtn.textContent = '▶';
      mPlayBtn.className = 'play-btn play-btn-lg';
      mPlayBtn.title = 'Ascolta anteprima iTunes';
    }}
  }}

  document.getElementById('modal-artist').textContent = s.artist;
  document.getElementById('modal-song').textContent = s.title;

  // Tab 1: brano singolo
  let songHtml = `<div class="modal-total">📻 ${{s.total}} passaggi totali</div>`;
  songHtml += buildDayBlocks(s.days);
  document.getElementById('tab-pane-song').innerHTML = songHtml;

  // Tab 2: tutti i brani dello stesso artista (da allSongs)
  const artistName = s.artist.toLowerCase();
  const artistSongs = allSongs
    .filter(x => x.artist.toLowerCase() === artistName)
    .sort((a,b) => b.total - a.total);

  document.getElementById('tab-artist-count').textContent = `(${{artistSongs.length}})`;

  // Aggrega tutti i passaggi dell'artista per data → [{time, title}, ...]
  const byDate = {{}};
  let artistTotal = 0;
  artistSongs.forEach(song => {{
    Object.entries(song.days).forEach(([date, times]) => {{
      if(!byDate[date]) byDate[date] = [];
      times.forEach(t => byDate[date].push({{time: t, title: song.title, year: song.year}}));
      artistTotal += times.length;
    }});
  }});

  const sortedArtistDates = Object.keys(byDate).sort((a,b) => dateToNum(b) - dateToNum(a));

  let artistHtml = `<div class="modal-total" style="gap:16px">
    🎤 ${{artistSongs.length}} brani &nbsp;·&nbsp; 📻 ${{artistTotal}} passaggi totali
  </div>`;

  sortedArtistDates.forEach(date => {{
    const entries = byDate[date].sort((a,b) => a.time.localeCompare(b.time));
    artistHtml += `<div class="day-block">
      <div class="day-header">
        <span class="day-date">📅 ${{date}}</span>
        <span class="day-count">${{entries.length}} passaggio/i</span>
      </div>
      <div style="display:flex;flex-direction:column;gap:5px">
        ${{entries.map(e => {{
          const eKey = (s.artist+'|'+e.title).toLowerCase();
          const ePrev = allSongs.find(x=>x.artist===s.artist&&x.title===e.title);
          const ePrevVal = ePrev && 'previewUrl' in ePrev ? String(ePrev.previewUrl) : '';
          return '<div style="display:flex;align-items:center;gap:8px">'
          + '<button class="play-btn" style="width:20px;height:20px;font-size:9px;flex-shrink:0" '
          + 'data-artist="' + esc(s.artist) + '" data-title="' + esc(e.title) + '" '
          + (ePrevVal ? 'data-preview="' + esc(ePrevVal) + '" ' : '')
          + 'onclick="event.stopPropagation();playPreviewBtn(this)" title="Ascolta anteprima">▶</button>'
          + (e.time !== 'In diretta' ? '<span class="time-chip">' + esc(e.time) + '</span>' : '')
          + '<span style="font-size:13px;color:var(--text);'+(e.title===s.title?'font-weight:700;color:var(--red)':'')+'">'
          + esc(e.title) + (e.year!=='N/A' ? ' <span style="font-size:10px;color:var(--text-muted);">('+e.year+')</span>' : '')
          + '</span></div>';
        }}).join('')}}
      </div>
    </div>`;
  }});
  document.getElementById('tab-pane-artist').innerHTML = artistHtml;

  // Mostra sempre la tab brano
  showModalTab('song');
  document.getElementById('modal-overlay').classList.add('open');
  document.body.style.overflow = 'hidden';
}}

function toggleArtistCard(id) {{
  const body = document.getElementById(id);
  const tog  = document.getElementById('tog-'+id);
  const open = body.style.display === 'block';
  body.style.display = open ? 'none' : 'block';
  tog.textContent = open ? '▼' : '▲';
}}

function showModalTab(tab) {{
  ['song','artist'].forEach(t => {{
    document.getElementById('tab-pane-'+t).classList.toggle('active', t===tab);
    document.getElementById('tab-btn-'+t).classList.toggle('active', t===tab);
  }});
}}

function closeModal(e) {{
  if(e.target === document.getElementById('modal-overlay')) closeModalDirect();
}}

function closeModalDirect() {{
  stopAudio();
  document.getElementById('modal-overlay').classList.remove('open');
  document.body.style.overflow = '';
}}

document.addEventListener('keydown', e => {{
  if(e.key === 'Escape') closeModalDirect();
}});

// ── ITUNES PREVIEW ───────────────────────────────────────────────────────────
let currentAudio    = null;
let currentPlayBtn  = null;
const previewCache  = {{}}; // 'artist|title' → url | null

async function playPreview(artist, title, btn, preloadedUrl) {{
  // Toggle: stessa canzone già caricata
  if(currentPlayBtn === btn && currentAudio) {{
    if(!currentAudio.paused) {{
      currentAudio.pause();
      btn.textContent = '▶';
      btn.classList.remove('playing');
    }} else {{
      currentAudio.play();
      btn.textContent = '⏸';
      btn.classList.add('playing');
    }}
    return;
  }}

  // Ferma riproduzione precedente
  stopAudio();

  // Mostra caricamento
  btn.textContent = '⏳';
  btn.classList.add('loading');
  btn.classList.remove('no-preview','playing');

  const key = (artist + '|' + title).toLowerCase();
  let url = previewCache[key];

  // URL pre-caricato da Python: usa solo se è iTunes (permanente).
  // URL Deezer (dzcdn.net) potrebbero essere scaduti → salta, usa ricerca live.
  if(url === undefined && preloadedUrl !== undefined) {{
    const isDeezer = preloadedUrl && preloadedUrl.includes('dzcdn.net');
    if(!isDeezer) {{
      url = preloadedUrl;        // iTunes o null = definitivo
      previewCache[key] = url;
    }}
    // Deezer: lascia url=undefined → cade nel blocco live sotto
  }}

  if(url === undefined) {{
    // ── Normalizzazione comune ────────────────────────────────────────────────
    const norm = s => (s||'').toLowerCase()
      .normalize('NFD').replace(/[\u0300-\u036f]/g,'')
      .replace(/[^a-z0-9 ]/g,' ').replace(/\s+/g,' ').trim();

    // ── Funzione punteggio generica ───────────────────────────────────────────
    const mkScorer = (getA, getT) => {{
      const sa = (r, a) => {{
        const ra = norm(getA(r)), al = norm(a);
        if(ra===al) return 8;
        if(ra.includes(al)||al.includes(ra)) return 5;
        return al.split(' ').filter(w=>w.length>2&&ra.includes(w)).length*2;
      }};
      const st = (r, t) => {{
        const rt = norm(getT(r)), tl = norm(t);
        if(rt===tl) return 8;
        if(rt.includes(tl)||tl.includes(rt)) return 5;
        return tl.split(' ').filter(w=>w.length>2&&rt.includes(w)).length*2;
      }};
      return (r, minA, minT) => (sa(r,artist)>=minA && st(r,title)>=minT)
        ? sa(r,artist)+st(r,title) : -1;
    }};

    const scoreITunes = mkScorer(r=>r.artistName||'', r=>r.trackName||'');
    const scoreDeezer = mkScorer(r=>r.artist?.name||'', r=>r.title||'');

    // ── Fetch con timeout (funziona da file:// verso HTTPS pubblici) ──────────
    const fetchJSON = (url, ms=6000) => {{
      const ctrl = new AbortController();
      const tid  = setTimeout(()=>ctrl.abort(), ms);
      return fetch(url, {{signal:ctrl.signal}})
        .then(r=>r.json())
        .finally(()=>clearTimeout(tid));
    }};

    // ── JSONP con timeout (fallback se fetch è bloccato) ─────────────────────
    const jsonp = (url, ms=6000) => new Promise((resolve, reject) => {{
      const tid = setTimeout(()=>{{ cleanup(); reject(new Error('timeout')); }}, ms);
      const cb  = '_cb' + Date.now().toString(36) + Math.random().toString(36).slice(2);
      const s   = document.createElement('script');
      const cleanup = () => {{ clearTimeout(tid); delete window[cb]; s.parentNode?.removeChild(s); }};
      window[cb] = d => {{ cleanup(); resolve(d); }};
      s.onerror  = () => {{ cleanup(); reject(new Error('jsonp err')); }};
      s.src = url + '&callback=' + cb;
      document.head.appendChild(s);
    }});

    // ── Recupera JSON provando fetch poi JSONP come fallback ─────────────────
    const getJSON = async (fetchUrl, jsonpUrl) => {{
      try   {{ return await fetchJSON(fetchUrl); }}
      catch {{ return await jsonp(jsonpUrl); }}
    }};

    // ── Cerca su iTunes ───────────────────────────────────────────────────────
    const findITunes = async (q, minA, minT) => {{
      const base = 'https://itunes.apple.com/search?term=' + encodeURIComponent(q)
                 + '&entity=song&limit=15&media=music';
      const data = await getJSON(base, base);   // iTunes usa stesso URL per fetch e JSONP
      const rs = (data.results||[])
        .filter(r => r.previewUrl && scoreITunes(r,minA,minT)>=0)
        .sort((a,b) => scoreITunes(b,minA,minT)-scoreITunes(a,minA,minT));
      return rs[0]?.previewUrl || null;
    }};

    // ── Cerca su Deezer ───────────────────────────────────────────────────────
    // Supporta ricerca avanzata: artist:"nome" track:"titolo"
    const findDeezer = async (q, minA, minT) => {{
      const base   = 'https://api.deezer.com/search?q=' + encodeURIComponent(q) + '&limit=15';
      const jsonpU = base + '&output=jsonp';
      const data   = await getJSON(base, jsonpU);
      const rs = (data.data||[])
        .filter(r => r.preview && scoreDeezer(r,minA,minT)>=0)
        .sort((a,b) => scoreDeezer(b,minA,minT)-scoreDeezer(a,minA,minT));
      return rs[0]?.preview || null;
    }};

    try {{
      // Round 1 – ricerca avanzata Deezer con campi separati + iTunes standard
      const deezerAdvanced = 'artist:"' + artist + '" track:"' + title + '"';
      const [r1, r2] = await Promise.all([
        findITunes(artist + ' ' + title, 3, 3).catch(()=>null),
        findDeezer(deezerAdvanced, 3, 3).catch(()=>null)
      ]);
      url = r1 || r2;

      // Round 2 – ricerca semplice Deezer "artista titolo"
      if(!url) {{
        const [r3, r4] = await Promise.all([
          findDeezer(artist + ' ' + title, 3, 3).catch(()=>null),
          findITunes(title, 5, 3).catch(()=>null)
        ]);
        url = r3 || r4;
      }}

      // Round 3 – solo titolo su Deezer (artista deve combaciare bene)
      if(!url) {{
        url = await findDeezer(title, 5, 3).catch(()=>null);
      }}
    }} catch(e) {{
      url = null;
    }}
    previewCache[key] = url;
  }}

  btn.classList.remove('loading');

  if(!url) {{
    btn.textContent = '✕';
    btn.classList.add('no-preview');
    btn.title = 'Anteprima non disponibile';
    // Ripristina dopo 2s
    setTimeout(() => {{
      if(btn.classList.contains('no-preview')) {{
        btn.textContent = '▶';
        btn.classList.remove('no-preview');
        btn.title = 'Ascolta anteprima iTunes';
      }}
    }}, 2000);
    return;
  }}

  btn.textContent = '⏸';
  btn.classList.add('playing');
  currentPlayBtn = btn;
  currentAudio   = new Audio(url);
  currentAudio.volume = 0.85;
  currentAudio.play().catch(() => {{
    btn.textContent = '✕';
    btn.classList.remove('playing');
    btn.classList.add('no-preview');
    currentAudio   = null;
    currentPlayBtn = null;
    setTimeout(() => {{
      btn.textContent = '▶';
      btn.classList.remove('no-preview');
    }}, 2000);
  }});
  currentAudio.onended = () => {{
    btn.textContent = '▶';
    btn.classList.remove('playing');
    currentAudio   = null;
    currentPlayBtn = null;
  }};
}}

// Usato dai pulsanti nel popup artista (legge data-* attributes)
function playPreviewBtn(btn) {{
  const artist     = btn.dataset.artist;
  const title      = btn.dataset.title;
  // previewUrl può essere stringa URL, stringa 'null', o assente
  const rawPrev    = btn.dataset.preview;
  const preloadUrl = rawPrev === undefined ? undefined
                   : rawPrev === 'null'    ? null
                   : rawPrev;
  playPreview(artist, title, btn, preloadUrl);
}}

function stopAudio() {{
  if(currentAudio) {{
    currentAudio.pause();
    currentAudio = null;
  }}
  if(currentPlayBtn) {{
    currentPlayBtn.textContent = '▶';
    currentPlayBtn.classList.remove('playing','loading','no-preview');
    currentPlayBtn = null;
  }}
}}

// INIT
const isOnlineConfigured = APPS_SCRIPT_URL && APPS_SCRIPT_URL !== "INSERISCI_QUI_URL_DELL_APPLICAZIONE_WEB";
let userRole = null;
let loggedInUser = null;

async function performLogin() {{
  const user = document.getElementById('login-username').value.trim();
  const pass = document.getElementById('login-password').value.trim();
  const errDiv = document.getElementById('login-error');
  const btn = document.getElementById('login-submit-btn');
  
  if (!user || !pass) {{
    errDiv.textContent = "Inserisci sia username che password.";
    errDiv.style.display = 'block';
    return;
  }}

  errDiv.style.display = 'none';
  btn.disabled = true;
  btn.querySelector('.btn-text').style.display = 'none';
  btn.querySelector('.btn-spinner').style.display = 'inline';

  try {{
    const loginUrl = `${{APPS_SCRIPT_URL}}?action=login&username=${{encodeURIComponent(user)}}&password=${{encodeURIComponent(pass)}}`;
    const res = await fetch(loginUrl);
    const data = await res.json();
    
    if (data.success) {{
      localStorage.setItem('radio_charts_user', user);
      localStorage.setItem('radio_charts_pass', pass);
      userRole = data.role;
      loggedInUser = user;
      document.getElementById('login-overlay').style.display = 'none';
      await fetchChartsData();
    }} else {{
      errDiv.textContent = data.error || "Credenziali non valide.";
      errDiv.style.display = 'block';
    }}
  }} catch (err) {{
    console.error(err);
    errDiv.textContent = "Errore di connessione con Google Sheets. Verifica la connessione o l'URL.";
    errDiv.style.display = 'block';
  }} finally {{
    btn.disabled = false;
    btn.querySelector('.btn-text').style.display = 'inline';
    btn.querySelector('.btn-spinner').style.display = 'none';
  }}
}}

async function fetchChartsData() {{
  const user = localStorage.getItem('radio_charts_user');
  const pass = localStorage.getItem('radio_charts_pass');
  if (!user || !pass) {{
    showLoginScreen();
    return;
  }}

  const tbody = document.getElementById('chart-body');
  if (tbody) {{
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:50px;font-weight:600;color:var(--text-muted)">Caricamento dei dati da Google Sheets in corso... ⏳</td></tr>';
  }}

  try {{
    const dataUrl = `${{APPS_SCRIPT_URL}}?action=getData&username=${{encodeURIComponent(user)}}&password=${{encodeURIComponent(pass)}}`;
    const res = await fetch(dataUrl);
    const result = await res.json();
    
    if (result.success) {{
      Object.keys(result.data).forEach(k => {{
        RAW[k] = result.data[k];
      }});
      userRole = result.role;
      loggedInUser = user;
      
      updateUserHeaderBadge();
      updateEditPermissions();
      switchRadio(currentRadio);
    }} else {{
      alert("Sessione scaduta o non valida: " + result.error);
      logout();
    }}
  }} catch (err) {{
    console.error(err);
    alert("Errore nel recupero dati da Google Sheets. Verranno usati i dati locali.");
    document.getElementById('login-overlay').style.display = 'none';
    userRole = 'user';
    updateEditPermissions();
    switchRadio(currentRadio);
  }}
}}

function showLoginScreen() {{
  document.getElementById('login-overlay').style.display = 'flex';
  document.getElementById('login-username').value = '';
  document.getElementById('login-password').value = '';
  document.getElementById('login-error').style.display = 'none';
}}

function logout() {{
  localStorage.removeItem('radio_charts_user');
  localStorage.removeItem('radio_charts_pass');
  userRole = null;
  loggedInUser = null;
  showLoginScreen();
}}

function updateUserHeaderBadge() {{
  const meta = document.querySelector('.header-meta');
  if (meta) {{
    let badge = document.getElementById('user-badge');
    if (!badge) {{
      badge = document.createElement('div');
      badge.id = 'user-badge';
      badge.style.marginTop = '6px';
      badge.style.fontSize = '12px';
      badge.style.background = 'rgba(255,255,255,0.1)';
      badge.style.padding = '4px 10px';
      badge.style.borderRadius = '20px';
      badge.style.display = 'inline-flex';
      badge.style.alignItems = 'center';
      badge.style.gap = '8px';
      meta.appendChild(badge);
    }}
    badge.innerHTML = `👤 <span>${{loggedInUser}} (${{userRole === 'admin' ? 'Admin' : 'Lettore'}})</span> <button onclick="logout()" style="background:none;border:none;color:var(--gold);font-weight:bold;cursor:pointer;font-size:11px;text-transform:uppercase;padding:0 2px">Esci</button>`;
  }}
}}

function updateEditPermissions() {{
  const isWritable = (userRole === 'admin');
  document.body.classList.toggle('user-is-admin', isWritable);
  document.body.classList.toggle('user-is-viewer', !isWritable);
}}

function initApp() {{
  if (isOnlineConfigured) {{
    const user = localStorage.getItem('radio_charts_user');
    const pass = localStorage.getItem('radio_charts_pass');
    if (user && pass) {{
      document.getElementById('login-overlay').style.display = 'none';
      fetchChartsData();
    }} else {{
      showLoginScreen();
    }}
  }} else {{
    document.getElementById('login-overlay').style.display = 'none';
    userRole = 'admin'; // offline sono tutti admin
    updateEditPermissions();
    switchRadio(currentRadio);
  }}
}}

initApp();

let editYearSong = null;

function openEditYearModal(event, index) {{
  event.stopPropagation();
  const s = renderedSongs[index];
  if (!s) return;
  
  editYearSong = {{ artist: s.artist, title: s.title, currentYear: s.year, currentRadioDate: s.radioDate || 'N/A' }};
  
  // Imposta i testi del modal
  document.getElementById('edit-year-artist').textContent = s.artist;
  document.getElementById('edit-year-title').textContent = s.title;
  
  // Imposta l'input dell'anno
  const inputYear = document.getElementById('edit-year-input');
  inputYear.value = s.year === 'N/A' ? '' : s.year;
  inputYear.disabled = false;

  // Imposta l'input della radio date
  const inputRadioDate = document.getElementById('edit-radiodate-input');
  const displayRD = s.radioDate === 'N/A' || s.radioDate === 'N/D' ? '' : s.radioDate;
  inputRadioDate.value = displayRD;
  inputRadioDate.disabled = false;
  
  // Reset banners e pulsanti
  document.getElementById('edit-year-error').style.display = 'none';
  document.getElementById('edit-year-success').style.display = 'none';
  document.getElementById('edit-year-form-content').style.display = 'block';
  
  const saveBtn = document.getElementById('edit-year-save-btn');
  saveBtn.disabled = false;
  saveBtn.querySelector('.btn-text').style.display = 'inline';
  saveBtn.querySelector('.btn-spinner').style.display = 'none';
  
  document.getElementById('edit-btn-cancel').disabled = false;

  // Reset del pulsante di ricerca
  const searchBtn = document.getElementById('edit-year-search-online-btn');
  if (searchBtn) {{
    searchBtn.disabled = false;
    searchBtn.querySelector('.btn-search-text').style.display = 'inline';
    searchBtn.querySelector('.btn-search-spinner').style.display = 'none';
  }}

  // Mostra il modal
  document.getElementById('edit-year-modal-overlay').classList.add('open');
  document.body.style.overflow = 'hidden';
  
  // Focus sull'input dell'anno
  setTimeout(() => inputYear.focus(), 100);
}}

async function searchSongDataOnline() {{
  if (!editYearSong) return;
  
  const searchBtn = document.getElementById('edit-year-search-online-btn');
  const textSpan = searchBtn.querySelector('.btn-search-text');
  const spinnerSpan = searchBtn.querySelector('.btn-search-spinner');
  const errBanner = document.getElementById('edit-year-error');
  
  // Disabilita pulsanti e mostra spinner
  searchBtn.disabled = true;
  textSpan.style.display = 'none';
  spinnerSpan.style.display = 'inline';
  errBanner.style.display = 'none';
  
  const inputYear = document.getElementById('edit-year-input');
  const inputRadioDate = document.getElementById('edit-radiodate-input');
  inputYear.disabled = true;
  inputRadioDate.disabled = true;
  document.getElementById('edit-btn-cancel').disabled = true;
  document.getElementById('edit-year-save-btn').disabled = true;
  
  try {{
    const res = await fetch('http://localhost:8000/api/search', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{
        artist: editYearSong.artist,
        title: editYearSong.title
      }})
    }});
    
    const data = await res.json();
    if (data.success) {{
      // Autocompila i campi
      if (data.year && data.year !== 'N/A') {{
        inputYear.value = data.year;
      }} else {{
        inputYear.value = '';
      }}
      if (data.radioDate && data.radioDate !== 'N/A' && data.radioDate !== 'N/D') {{
        inputRadioDate.value = data.radioDate;
      }} else {{
        inputRadioDate.value = '';
      }}
      
      // Imposta il focus sul tasto salva
      document.getElementById('edit-year-save-btn').focus();
    }} else {{
      errBanner.textContent = "Errore durante la ricerca: " + data.error;
      errBanner.style.display = 'block';
    }}
  }} catch (err) {{
    console.error(err);
    errBanner.textContent = "Il server locale non risponde. Assicurati che server.py sia attivo!";
    errBanner.style.display = 'block';
  }} finally {{
    // Ripristina stato pulsanti/input
    searchBtn.disabled = false;
    textSpan.style.display = 'inline';
    spinnerSpan.style.display = 'none';
    
    inputYear.disabled = false;
    inputRadioDate.disabled = false;
    document.getElementById('edit-btn-cancel').disabled = false;
    document.getElementById('edit-year-save-btn').disabled = false;
  }}
}}

function closeEditYearModal(e) {{
  if (e.target === document.getElementById('edit-year-modal-overlay')) {{
    closeEditYearModalDirect();
  }}
}}

function closeEditYearModalDirect() {{
  document.getElementById('edit-year-modal-overlay').classList.remove('open');
  // Se non c'è nessun altro modal aperto, sblocca lo scroll del body
  if (!document.getElementById('modal-overlay').classList.contains('open')) {{
    document.body.style.overflow = '';
  }}
}}

async function saveYearOverride() {{
  if (!editYearSong) return;
  const inputYear = document.getElementById('edit-year-input');
  const yearVal = inputYear.value.trim();
  
  if (yearVal && (!/^\d{{4}}$/.test(yearVal) || parseInt(yearVal) < 1900 || parseInt(yearVal) > 2100)) {{
    showEditError("Inserisci un anno valido a 4 cifre (es. 1995) o lascia vuoto!");
    return;
  }}

  const inputRadioDate = document.getElementById('edit-radiodate-input');
  const radioDateVal = inputRadioDate.value.trim();
  
  if (radioDateVal && !/^\d{{2}}\/\d{{2}}\/\d{{4}}$/.test(radioDateVal)) {{
    showEditError("La Radio Date deve essere nel formato GG/MM/AAAA (es. 15/05/2026) o lasciata vuota!");
    return;
  }}
  
  // Validazione reale della data
  if (radioDateVal) {{
    const parts = radioDateVal.split('/');
    const d = parseInt(parts[0]), m = parseInt(parts[1]), y = parseInt(parts[2]);
    const dt = new Date(y, m - 1, d);
    if (dt.getFullYear() !== y || dt.getMonth() !== m - 1 || dt.getDate() !== d) {{
      showEditError("Inserisci una data reale valida (es. 29/02/2024 è bisestile, 31/11/2026 non esiste)!");
      return;
    }}
  }}
  
  const targetYear = yearVal || 'N/A';
  const targetRadioDate = radioDateVal || 'N/A';
  
  // Caricamento...
  inputYear.disabled = true;
  inputRadioDate.disabled = true;
  document.getElementById('edit-btn-cancel').disabled = true;
  const saveBtn = document.getElementById('edit-year-save-btn');
  saveBtn.disabled = true;
  saveBtn.querySelector('.btn-text').style.display = 'none';
  saveBtn.querySelector('.btn-spinner').style.display = 'inline';
  document.getElementById('edit-year-error').style.display = 'none';
  
  try {{
    let res, data;
    const isOnline = APPS_SCRIPT_URL && APPS_SCRIPT_URL !== "INSERISCI_QUI_URL_DELL_APPLICAZIONE_WEB";
    
    if (isOnline) {{
      const bodyData = {{
        action: "saveOverride",
        username: localStorage.getItem('radio_charts_user'),
        password: localStorage.getItem('radio_charts_pass'),
        artist: editYearSong.artist,
        title: editYearSong.title,
        year: targetYear,
        radioDate: targetRadioDate
      }};
      res = await fetch(APPS_SCRIPT_URL, {{
        method: 'POST',
        body: JSON.stringify(bodyData)
      }});
      data = await res.json();
    }} else {{
      res = await fetch('http://localhost:8000/api/override', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{
          artist: editYearSong.artist,
          title: editYearSong.title,
          year: targetYear,
          radioDate: targetRadioDate
        }})
      }});
      data = await res.json();
    }}
    
    const dataObj = data; // Per compatibilità col codice successivo che usa data.success

    if (data.success) {{
      // Successo: mostra il banner di successo con l'animazione checkmark
      document.getElementById('edit-year-form-content').style.display = 'none';
      document.getElementById('edit-year-success').style.display = 'flex';
      
      // Aggiorna inline in memoria
      if (isGlobale) {{
        const targetNormKey = getNormKey(editYearSong.artist, editYearSong.title);
        allSongs.forEach(s => {{
          if (getNormKey(s.artist, s.title) === targetNormKey) {{
            s.year = targetYear;
            s.radioDate = targetRadioDate;
          }}
        }});
        
        RADIO_KEYS.forEach(radioKey => {{
          RAW[radioKey].songs.forEach(s => {{
            if (getNormKey(s.artist, s.title) === targetNormKey) {{
              s.year = targetYear;
              s.radioDate = targetRadioDate;
            }}
          }});
        }});
      }} else {{
        const songInAll = allSongs.find(s => s.artist === editYearSong.artist && s.title === editYearSong.title);
        if (songInAll) {{
          songInAll.year = targetYear;
          songInAll.radioDate = targetRadioDate;
        }}
        const songInRaw = RAW[currentRadio].songs.find(s => s.artist === editYearSong.artist && s.title === editYearSong.title);
        if (songInRaw) {{
          songInRaw.year = targetYear;
          songInRaw.radioDate = targetRadioDate;
        }}
      }}
      
      // 3. Rigenera decade chips e riapplica filtri
      buildDecadeChips();
      applyFilters();
      
      // Chiudi il modal dopo 1.5 secondi
      setTimeout(() => {{
        closeEditYearModalDirect();
      }}, 1500);
      
    }} else {{
      showEditError("Errore dal server: " + data.error);
    }}
  }} catch (err) {{
    console.error(err);
    showEditError("Il server locale non risponde. Assicurati che server.py sia attivo!");
  }}
}}

function showEditError(msg) {{
  const errBanner = document.getElementById('edit-year-error');
  errBanner.textContent = msg;
  errBanner.style.display = 'block';
  
  // Ripristina stato pulsanti/input
  const inputYear = document.getElementById('edit-year-input');
  inputYear.disabled = false;
  const inputRadioDate = document.getElementById('edit-radiodate-input');
  inputRadioDate.disabled = false;
  document.getElementById('edit-btn-cancel').disabled = false;
  
  const saveBtn = document.getElementById('edit-year-save-btn');
  saveBtn.disabled = false;
  saveBtn.querySelector('.btn-text').style.display = 'inline';
  saveBtn.querySelector('.btn-spinner').style.display = 'none';
}}
</script>
</body>
</html>"""

with open(OUT_HTML, 'w', encoding='utf-8') as f:
    f.write(html)

size_kb = os.path.getsize(OUT_HTML) // 1024
print(f"\nHTML generato: {OUT_HTML}")
print(f"Dimensione: {size_kb} KB")
print("Fatto!")
