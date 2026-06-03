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
BIRIKINA_JSON  = os.path.join(BASE, 'radio_birikina_history.json')
BRUNO_JSON     = os.path.join(BASE, 'radio_bruno_history.json')
KISSKISS_JSON  = os.path.join(BASE, 'radio_kisskiss_history.json')
M2O_JSON       = os.path.join(BASE, 'radio_m2o_history.json')
PROPOSTAAOSTA_JSON = os.path.join(BASE, 'radio_propostaaosta_history.json')
CAPITAL_JSON   = os.path.join(BASE, 'radio_capital_history.json')
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
    
    # Strip leading or trailing parenthetical parts (e.g. "(I've Had) The Time of My Life" -> "The Time of My Life")
    title_clean = re.sub(r'^\s*\([^)]+\)\s*', '', title_clean)
    title_clean = re.sub(r'\s*\([^)]+\)\s*$', '', title_clean)
    
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
    r'kiss\s*kiss|monte\s*carlo|studio\s*54|studio54|network|antenna|birikina|bruno|proposta)$',
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

birikina_history = []
if os.path.exists(BIRIKINA_JSON):
    with open(BIRIKINA_JSON, 'r', encoding='utf-8') as f:
        birikina_history = json.load(f)

bruno_history = []
if os.path.exists(BRUNO_JSON):
    with open(BRUNO_JSON, 'r', encoding='utf-8') as f:
        bruno_history = json.load(f)

kisskiss_history = []
if os.path.exists(KISSKISS_JSON):
    with open(KISSKISS_JSON, 'r', encoding='utf-8') as f:
        kisskiss_history = json.load(f)

m2o_history = []
if os.path.exists(M2O_JSON):
    with open(M2O_JSON, 'r', encoding='utf-8') as f:
        m2o_history = json.load(f)

propostaaosta_history = []
if os.path.exists(PROPOSTAAOSTA_JSON):
    with open(PROPOSTAAOSTA_JSON, 'r', encoding='utf-8') as f:
        propostaaosta_history = json.load(f)

capital_history = []
if os.path.exists(CAPITAL_JSON):
    with open(CAPITAL_JSON, 'r', encoding='utf-8') as f:
        capital_history = json.load(f)

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
for history in [subasio_history, divina_history, mitology_history, nostalgia_history, toscana_history, italia_history, rds_history, rtl1025_history, birikina_history, bruno_history, kisskiss_history, m2o_history, propostaaosta_history, capital_history]:
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

print("Elaborazione Radio Birikina...")
birikina_ranked, birikina_dates_sorted = process_generic_radio(birikina_history, "Radio Birikina")

print("Elaborazione Radio Bruno...")
bruno_ranked, bruno_dates_sorted = process_generic_radio(bruno_history, "Radio Bruno")

print("Elaborazione Radio Kiss Kiss...")
kisskiss_ranked, kisskiss_dates_sorted = process_generic_radio(kisskiss_history, "Radio Kiss Kiss")

print("Elaborazione Radio m2o...")
m2o_ranked, m2o_dates_sorted = process_generic_radio(m2o_history, "Radio m2o")

print("Elaborazione Proposta Aosta...")
propostaaosta_ranked, propostaaosta_dates_sorted = process_generic_radio(propostaaosta_history, "Proposta Aosta")

print("Elaborazione Radio Capital...")
capital_ranked, capital_dates_sorted = process_generic_radio(capital_history, "Radio Capital")

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
raw_birikina  = make_radio_data(birikina_ranked,  birikina_dates_sorted)
raw_bruno     = make_radio_data(bruno_ranked,     bruno_dates_sorted)
raw_kisskiss  = make_radio_data(kisskiss_ranked,  kisskiss_dates_sorted)
raw_m2o       = make_radio_data(m2o_ranked,       m2o_dates_sorted)
raw_propostaaosta = make_radio_data(propostaaosta_ranked, propostaaosta_dates_sorted)
raw_capital   = make_radio_data(capital_ranked,   capital_dates_sorted)

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
        'rtl1025': raw_rtl1025,
        'birikina': raw_birikina,
        'bruno': raw_bruno,
        'kisskiss': raw_kisskiss,
        'm2o': raw_m2o,
        'propostaaosta': raw_propostaaosta,
        'capital': raw_capital
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
json_birikina  = json.dumps(raw_birikina,  ensure_ascii=False, separators=(',', ':'))
json_bruno     = json.dumps(raw_bruno,     ensure_ascii=False, separators=(',', ':'))
json_kisskiss  = json.dumps(raw_kisskiss,  ensure_ascii=False, separators=(',', ':'))
json_m2o       = json.dumps(raw_m2o,       ensure_ascii=False, separators=(',', ':'))
json_propostaaosta = json.dumps(raw_propostaaosta, ensure_ascii=False, separators=(',', ':'))
json_capital   = json.dumps(raw_capital,   ensure_ascii=False, separators=(',', ':'))

print(f"  JSON Subasio:   {len(json_subasio)//1024} KB")
print(f"  JSON Divina:    {len(json_divina)//1024} KB")
print(f"  JSON Mitology:  {len(json_mitology)//1024} KB")
print(f"  JSON Nostalgia: {len(json_nostalgia)//1024} KB")
print(f"  JSON Toscana:   {len(json_toscana)//1024} KB")
print(f"  JSON Italia:    {len(json_italia)//1024} KB")
print(f"  JSON RDS:       {len(json_rds)//1024} KB")
print(f"  JSON RTL 102.5: {len(json_rtl1025)//1024} KB")
print(f"  JSON Birikina:  {len(json_birikina)//1024} KB")
print(f"  JSON Bruno:     {len(json_bruno)//1024} KB")
print(f"  JSON Kiss Kiss: {len(json_kisskiss)//1024} KB")
print(f"  JSON m2o:       {len(json_m2o)//1024} KB")
print(f"  JSON Proposta:  {len(json_propostaaosta)//1024} KB")
print(f"  JSON Capital:   {len(json_capital)//1024} KB")

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
  --red:#C8102E; --red-dark:#9e0c24; --gold:#facc15; --silver:#C0C0C0; --bronze:#CD7F32;
  --bg:#f8fafc; --surface:#fff; --border:#e2e8f0;
  --text:#0f172a; --text-muted:#475569; --text-light:#94a3b8;
  --up:#22c55e; --down:#ef4444; --new:#3b82f6; --stable:#64748b;
  --top10:#fff3cd; --top3-bg:#fff;
}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Segoe UI',system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--text);min-height:100vh}}

/* HEADER */
header{{background:linear-gradient(135deg,#0f172a 0%,#1e293b 100%);color:#fff;padding:0;box-shadow:0 4px 20px rgba(0,0,0,.25)}}
.header-top{{display:flex;align-items:center;justify-content:space-between;padding:18px 32px 12px}}
.logo{{display:flex;align-items:center;gap:12px}}
.logo-icon{{width:44px;height:44px;background:var(--red);border:2px solid var(--gold);border-radius:10px;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:22px;color:#fff}}
.logo-text h1{{font-size:22px;font-weight:800;letter-spacing:.5px}}
.logo-text span{{font-size:11px;opacity:.6;text-transform:uppercase;letter-spacing:2px}}
.header-meta{{text-align:right;font-size:12px;opacity:.8}}
.header-meta strong{{display:block;font-size:14px;opacity:1;color:var(--gold);margin-top:2px}}

/* RADIO TABS */
.radio-tabs{{display:flex;padding:0 32px;border-top:1px solid rgba(255,255,255,.08);overflow-x:auto;white-space:nowrap;-webkit-overflow-scrolling:touch}}
.radio-tabs::-webkit-scrollbar{{height:6px;display:block}}
.radio-tabs::-webkit-scrollbar-track{{background:rgba(255,255,255,0.02)}}
.radio-tabs::-webkit-scrollbar-thumb{{background:rgba(255,255,255,0.15);border-radius:3px}}
.radio-tab{{padding:14px 28px;font-size:14px;font-weight:600;cursor:pointer;border:none;background:transparent;color:rgba(255,255,255,.55);border-bottom:3px solid transparent;transition:all .2s;letter-spacing:.5px;text-transform:uppercase;flex-shrink:0}}
.radio-tab:hover{{color:rgba(255,255,255,.9)}}
.radio-tab.active{{color:#fff;border-bottom-color:#facc15}}

/* FILTERS */
.filters-bar {{
  background: #fff;
  border-radius: 16px;
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  box-shadow: 0 4px 20px rgba(15,23,42,.04), 0 1px 3px rgba(15,23,42,.02);
  border: 1px solid rgba(15,23,42,.06);
  margin: 20px 32px 0;
}}
.filter-row {{
  display: flex;
  align-items: center;
  gap: 16px;
  width: 100%;
}}
.row-1 {{
  justify-content: space-between;
}}
.search-box{{position:relative;flex:1;min-width:200px;max-width:380px}}
.search-box input{{width:100%;padding:10px 40px 10px 14px;border:1.5px solid var(--border);border-radius:10px;font-size:14px;outline:none;transition:all .2s;background:#f8fafc}}
.search-box input:focus{{border-color:#3b82f6;background:#fff;box-shadow:0 0 0 3px rgba(59,130,246,.1)}}
.search-box .icon{{position:absolute;right:14px;top:50%;transform:translateY(-50%);color:var(--text-muted);font-size:16px;pointer-events:none}}

.filter-grid {{
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  gap: 24px;
  align-items: flex-start;
  padding-bottom: 16px;
  border-bottom: 1px solid #f1f5f9;
}}
.filter-section {{
  display: flex;
  flex-direction: column;
  gap: 8px;
}}
.select-wrapper {{
  position: relative;
  display: inline-flex;
  align-items: center;
}}
.select-icon {{
  position: absolute;
  left: 12px;
  font-size: 14px;
  pointer-events: none;
  z-index: 10;
}}
.styled-select {{
  padding: 10px 36px 10px 34px;
  border: 1.5px solid #cbd5e1;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  outline: none;
  background-color: #fff;
  color: #334155;
  cursor: pointer;
  appearance: none;
  -webkit-appearance: none;
  background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e");
  background-repeat: no-repeat;
  background-position: right 12px center;
  background-size: 14px;
  transition: all 0.2s ease;
  width: 100%;
}}
.styled-select:focus {{
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}}
.styled-select.text-red {{
  color: var(--red);
  border-color: rgba(200, 16, 46, 0.3);
  background-color: rgba(200, 16, 46, 0.01);
  background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23C8102E' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e");
}}
.styled-select.text-red:focus {{
  border-color: var(--red);
  box-shadow: 0 0 0 3px rgba(200, 16, 46, 0.1);
}}

.row-3 {{
  justify-content: flex-start;
  gap: 32px;
  flex-wrap: wrap;
}}
.adv-group {{
  display: flex;
  flex-direction: column;
  gap: 8px;
}}
.compact-select {{
  padding: 8px 32px 8px 12px;
  background-position: right 8px center;
  font-size: 13px;
  border-radius: 8px;
  width: auto;
  min-width: 90px;
}}
.compact-input {{
  padding: 8px 12px;
  border: 1.5px solid #cbd5e1;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  outline: none;
  background-color: #fff;
  color: #334155;
  transition: all 0.2s ease;
  width: 90px;
}}
.compact-input:focus {{
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}}

.decade-chips{{display:flex;gap:6px;flex-wrap:wrap}}
.chip{{padding:6px 14px;border-radius:20px;font-size:12px;font-weight:600;cursor:pointer;border:1.5px solid #e2e8f0;background:#f8fafc;color:#475569;transition:all .2s;white-space:nowrap}}
.chip:hover{{border-color:var(--red);color:var(--red);background:rgba(200,16,46,0.02)}}
.chip.active{{background:var(--red);color:#fff;border-color:var(--red);box-shadow:0 4px 12px rgba(200, 16, 46, 0.2)}}
.filter-label{{font-size:11px;color:var(--text-muted);font-weight:700;text-transform:uppercase;letter-spacing:.8px;white-space:nowrap}}

/* TOGGLE SWITCH STYLE */
.toggle-wrap {{
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
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

.info-tooltip {{
  cursor: help;
  color: var(--text-light);
  display: inline-block;
  margin-left: 2px;
}}

/* RESULTS COUNT */
.results-count-wrap{{margin-left:auto;display:flex;align-items:center}}
.results-count{{font-size:13px;font-weight:600;color:var(--text-muted);white-space:nowrap}}

/* MAIN TABLE */
.table-wrap{{padding:24px 32px;overflow-x:auto}}
table{{width:100%;border-collapse:collapse;font-size:14px}}
thead tr{{background:#0f172a;color:#fff}}
thead th{{padding:14px 16px;text-align:left;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.8px;white-space:nowrap;cursor:pointer;user-select:none;transition:background .15s}}
thead th:hover{{background:rgba(255,255,255,.05)}}
thead th.sorted-asc::after{{content:' ▲';color:var(--gold)}}
thead th.sorted-desc::after{{content:' ▼';color:var(--gold)}}
thead th.sorted-asc.sorted-multi::after{{content:' ▲' attr(data-sort-index);font-size:10px;color:#bbb;margin-left:2px}}
thead th.sorted-desc.sorted-multi::after{{content:' ▼' attr(data-sort-index);font-size:10px;color:#bbb;margin-left:2px}}
thead th:first-child{{cursor:default}}
tbody tr{{border-bottom:1px solid var(--border);transition:background .15s;background:#fff}}
tbody tr:hover{{background:#f8fafc}}
td{{padding:12px 16px;vertical-align:middle}}

/* POSITION */
.pos-cell{{text-align:center;width:60px;padding-right:0 !important}}
.pos-badge{{width:32px;height:32px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-size:13px;font-weight:800;margin:0 auto}}
.pos-1{{background:#ffd54f;color:#7f5f00;box-shadow:0 2px 6px rgba(255,213,79,.3)}}
.pos-2{{background:#cbd5e1;color:#475569}}
.pos-3{{background:#ffb74d;color:#7c2d12}}
.pos-top10{{background:#f1f5f9;color:#475569}}
.pos-rest{{background:#f8fafc;color:var(--text-light)}}

/* TREND */
.trend-cell{{width:45px;text-align:center;padding-left:0 !important}}
.trend{{font-size:11px;font-weight:700;padding:3px 6px;border-radius:6px;display:inline-block;white-space:nowrap}}
.trend-up{{color:var(--up);background:#dcfce7}}
.trend-down{{color:var(--down);background:#fee2e2}}
.trend-new{{color:var(--new);background:#dbeafe;font-size:10px;letter-spacing:.5px}}
.trend-stable{{color:var(--stable);background:#f1f5f9}}

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
    display: flex;
    flex-direction: column;
    align-items: stretch;
  }}
  .filter-row{{
    display: flex; /* Attiva le righe separate solo su mobile */
    align-items: center;
    gap: 8px;
    width: 100%;
    flex-wrap: nowrap;
  }}
  .main-filter-row{{
    justify-content: space-between;
  }}
  .search-box{{
    max-width: none;
    width: 100%;
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
  padding: 10px 32px;
  flex-direction: column;
  align-items: stretch;
  gap: 0;
}}
.global-selector-bar.show {{
  display: flex;
}}
.global-selector-header {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  user-select: none;
  padding: 4px 0;
}}
.global-selector-summary {{
  font-size: 13px;
  font-weight: 600;
  color: var(--text-muted);
}}
.global-selector-summary strong {{
  color: #0d9488;
}}
.global-toggle-btn {{
  background: transparent;
  border: none;
  font-weight: 700;
  color: #0d9488;
  cursor: pointer;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 4px 8px;
  border-radius: 6px;
  transition: all 0.15s ease;
}}
.global-toggle-btn:hover {{
  background: rgba(13, 148, 136, 0.08);
}}
.global-selector-body {{
  display: none;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  border-top: 1px solid var(--border);
  padding-top: 12px;
  margin-top: 8px;
  animation: slideDown 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}}
.global-selector-body.open {{
  display: flex;
}}
@keyframes slideDown {{
  from {{ opacity: 0; transform: translateY(-5px); }}
  to {{ opacity: 1; transform: translateY(0); }}
}}
.global-checkboxes-container {{
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}}
.global-selector-label {{
  font-size: 11px;
  font-weight: 700;
  color: var(--text-muted);
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


/* === RESTYLE V2 AUTOMATICALLY APPLIED === */
/* =========================================================
   RADIO CHARTS - RESTYLE V2
   Incolla questo blocco ALLA FINE dello <style> esistente.
   Se avevi già incollato altri CSS correttivi, rimuovili oppure
   lascia questo per ultimo.
   ========================================================= */

:root {{
  --rc-bg: #f4f7fb;
  --rc-panel: #ffffff;
  --rc-panel-soft: #f8fafc;
  --rc-navy: #071124;
  --rc-navy-2: #101a30;
  --rc-navy-3: #17243b;
  --rc-red: #d80b35;
  --rc-red-dark: #b2072b;
  --rc-teal: #0f9f90;
  --rc-teal-dark: #0b7f74;
  --rc-yellow: #facc15;
  --rc-border: #e6ebf2;
  --rc-border-strong: #d5dde8;
  --rc-text: #0f172a;
  --rc-muted: #64748b;
  --rc-shadow: 0 18px 45px rgba(15, 23, 42, .10);
  --rc-shadow-soft: 0 8px 24px rgba(15, 23, 42, .07);
  --rc-radius: 24px;
}}

* {{
  box-sizing: border-box;
}}

html {{
  background: var(--rc-bg);
}}

body {{
  background:
    radial-gradient(circle at top left, rgba(13, 148, 136, .08), transparent 28rem),
    linear-gradient(180deg, #f7f9fc 0%, #f2f6fb 100%) !important;
  color: var(--rc-text);
  overflow-x: hidden;
}}

/* =========================================================
   HEADER
   ========================================================= */

header {{
  background:
    radial-gradient(circle at 12% 0%, rgba(216, 11, 53, .18), transparent 22rem),
    linear-gradient(135deg, #071124 0%, #111c33 62%, #18253f 100%) !important;
  box-shadow: 0 14px 38px rgba(3, 8, 20, .32) !important;
  position: relative;
  z-index: 5;
}}

.header-top {{
  max-width: 1180px;
  margin: 0 auto;
  padding: 24px 28px 20px !important;
  display: flex !important;
  align-items: center !important;
  justify-content: space-between !important;
  gap: 18px !important;
}}

.logo {{
  min-width: 0;
  gap: 16px !important;
}}

.logo-icon {{
  width: 58px !important;
  height: 58px !important;
  border-radius: 18px !important;
  background: linear-gradient(145deg, #e40d3d, #b8072c) !important;
  border: 2px solid rgba(250, 204, 21, .9) !important;
  box-shadow: 0 10px 24px rgba(216, 11, 53, .28), inset 0 1px 0 rgba(255,255,255,.28) !important;
  font-size: 26px !important;
  flex: 0 0 auto;
}}

.logo-text h1 {{
  font-size: clamp(28px, 3.4vw, 42px) !important;
  line-height: .95 !important;
  letter-spacing: -.8px !important;
  font-weight: 900 !important;
}}

.logo-text span {{
  display: block;
  margin-top: 9px;
  font-size: clamp(12px, 1.4vw, 17px) !important;
  letter-spacing: .24em !important;
  opacity: .66 !important;
  font-weight: 600 !important;
}}

.header-meta {{
  text-align: right !important;
  font-size: 14px !important;
  color: rgba(255,255,255,.78) !important;
  opacity: 1 !important;
  line-height: 1.2 !important;
  flex: 0 0 auto;
}}

.header-meta strong {{
  display: block !important;
  margin-top: 5px !important;
  color: var(--rc-yellow) !important;
  font-size: clamp(18px, 2vw, 25px) !important;
  font-weight: 900 !important;
  letter-spacing: -.3px !important;
}}

#user-badge {{
  margin-top: 11px !important;
  padding: 8px 14px !important;
  border-radius: 999px !important;
  background: rgba(255,255,255,.10) !important;
  border: 1px solid rgba(255,255,255,.08) !important;
  color: rgba(255,255,255,.86) !important;
  font-size: 13px !important;
  gap: 10px !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.05) !important;
}}

#user-badge button {{
  color: var(--rc-yellow) !important;
  font-size: 12px !important;
}}

/* =========================================================
   TAB RADIO
   ========================================================= */

.radio-tabs {{
  max-width: 1180px;
  margin: 0 auto;
  padding: 0 28px !important;
  border-top: 1px solid rgba(255,255,255,.08) !important;
  display: flex !important;
  gap: 0 !important;
  overflow-x: auto !important;
  white-space: nowrap !important;
  scrollbar-width: none;
  cursor: grab;
  user-select: none;
}}

.radio-tabs.active-drag {{
  cursor: grabbing;
}}

.radio-tabs::-webkit-scrollbar {{
  display: none !important;
}}

.radio-tab {{
  position: relative;
  padding: 18px 24px 19px !important;
  color: rgba(255,255,255,.56) !important;
  font-size: 15px !important;
  font-weight: 800 !important;
  letter-spacing: .045em !important;
  border-bottom: none !important;
  transition: color .18s ease, background .18s ease !important;
  flex-shrink: 0 !important;
}}

.radio-tab:hover {{
  color: rgba(255,255,255,.92) !important;
  background: rgba(255,255,255,.035) !important;
}}

.radio-tab.active,
.radio-tab.globale.active {{
  color: var(--rc-yellow) !important;
}}

.radio-tab.active::after,
.radio-tab.globale.active::after {{
  content: "";
  position: absolute;
  left: 18px;
  right: 18px;
  bottom: 0;
  height: 5px;
  border-radius: 999px 999px 0 0;
  background: var(--rc-yellow);
  box-shadow: 0 -4px 12px rgba(250, 204, 21, .25);
}}

/* =========================================================
   SELETTORE GLOBALE
   ========================================================= */

.global-selector-bar {{
  max-width: 1180px;
  margin: 18px auto 0 !important;
  padding: 0 28px !important;
  background: transparent !important;
  border: 0 !important;
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
}}

.global-selector-bar.show {{
  display: flex !important;
}}

.global-selector-header {{
  width: 100%;
  min-height: 60px;
  padding: 14px 22px !important;
  border-radius: 20px !important;
  background: rgba(255,255,255,.82) !important;
  border: 1px solid rgba(226,232,240,.95) !important;
  box-shadow: var(--rc-shadow-soft) !important;
}}

.global-selector-summary {{
  font-size: 17px !important;
  color: #334155 !important;
  font-weight: 750 !important;
}}

.global-selector-summary strong {{
  color: var(--rc-teal) !important;
  font-weight: 900 !important;
}}

.global-toggle-btn {{
  padding: 8px 12px !important;
  border-radius: 999px !important;
  color: var(--rc-teal) !important;
  background: rgba(15,159,144,.08) !important;
  font-size: 14px !important;
}}

.global-selector-body.open {{
  display: flex !important;
  width: 100%;
  margin-top: 12px !important;
  padding: 18px !important;
  border-radius: 20px !important;
  border: 1px solid var(--rc-border) !important;
  background: #fff !important;
  box-shadow: var(--rc-shadow-soft) !important;
}}

.global-checkboxes {{
  gap: 8px !important;
}}

.global-cb-wrap {{
  border-radius: 999px !important;
  padding: 8px 12px !important;
  background: #f8fafc !important;
}}

/* =========================================================
   PANNELLO FILTRI
   ========================================================= */

.filters-bar {{
  width: min(1124px, calc(100% - 56px)) !important;
  margin: 22px auto 28px !important;
  padding: 26px !important;
  border-radius: var(--rc-radius) !important;
  background:
    linear-gradient(180deg, rgba(255,255,255,.98), rgba(255,255,255,.94)) !important;
  border: 1px solid rgba(226,232,240,.92) !important;
  box-shadow: var(--rc-shadow) !important;
  display: flex !important;
  flex-direction: column !important;
  gap: 22px !important;
  overflow: hidden !important;
}}

.filter-row,
.row-1,
.row-3 {{
  width: 100% !important;
}}

.row-1 {{
  display: grid !important;
  grid-template-columns: minmax(0, 1fr) 180px 160px !important;
  align-items: stretch !important;
  gap: 18px !important;
}}

.search-box {{
  max-width: none !important;
  width: 100% !important;
  min-width: 0 !important;
}}

.search-box input {{
  width: 100% !important;
  height: 58px !important;
  padding: 0 58px 0 22px !important;
  border-radius: 17px !important;
  border: 1.5px solid var(--rc-border-strong) !important;
  background: #fbfdff !important;
  color: var(--rc-text) !important;
  font-size: 18px !important;
  font-weight: 500 !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.7) !important;
}}

.search-box input:focus {{
  border-color: rgba(15, 159, 144, .72) !important;
  background: #fff !important;
  box-shadow: 0 0 0 4px rgba(15, 159, 144, .12) !important;
}}

.search-box .icon {{
  right: 20px !important;
  font-size: 23px !important;
  color: #334155 !important;
}}

.export-btn,
#export-btn {{
  width: 100% !important;
  height: 58px !important;
  margin-left: 0 !important;
  padding: 0 20px !important;
  border-radius: 17px !important;
  background: linear-gradient(145deg, #10a796, #078477) !important;
  color: #fff !important;
  border: 0 !important;
  display: inline-flex !important;
  justify-content: center !important;
  align-items: center !important;
  gap: 10px !important;
  font-size: 18px !important;
  font-weight: 900 !important;
  letter-spacing: -.2px !important;
  box-shadow: 0 12px 22px rgba(15, 159, 144, .25) !important;
}}

.export-btn:hover,
#export-btn:hover {{
  background: linear-gradient(145deg, #0f9f90, #07756b) !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 15px 26px rgba(15, 159, 144, .32) !important;
}}

.export-icon {{
  width: 19px !important;
  height: 19px !important;
}}

.filter-label {{
  display: block !important;
  color: #475569 !important;
  font-size: 13px !important;
  line-height: 1.15 !important;
  font-weight: 900 !important;
  text-transform: uppercase !important;
  letter-spacing: .09em !important;
}}

.filter-grid {{
  display: grid !important;
  grid-template-columns: minmax(360px, 1.7fr) minmax(180px, .7fr) minmax(180px, .7fr) !important;
  align-items: start !important;
  gap: 28px !important;
  padding: 22px 0 24px !important;
  border-top: 1px solid #f0f3f7 !important;
  border-bottom: 1px solid #edf1f5 !important;
}}

.filter-section {{
  display: flex !important;
  flex-direction: column !important;
  gap: 13px !important;
  min-width: 0 !important;
}}

.decade-chips {{
  display: grid !important;
  grid-template-columns: repeat(4, minmax(78px, 1fr)) !important;
  gap: 10px !important;
  width: 100% !important;
}}

.chip {{
  height: 42px !important;
  min-width: 0 !important;
  padding: 0 12px !important;
  border-radius: 999px !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  background: #f9fbfd !important;
  border: 1.5px solid #dbe3ee !important;
  color: #475569 !important;
  font-size: 15px !important;
  font-weight: 850 !important;
  box-shadow: 0 1px 2px rgba(15,23,42,.03) !important;
}}

.chip:hover {{
  color: var(--rc-red) !important;
  border-color: rgba(216, 11, 53, .40) !important;
  background: #fff8fa !important;
}}

.chip.active {{
  color: #fff !important;
  background: linear-gradient(145deg, var(--rc-red), var(--rc-red-dark)) !important;
  border-color: transparent !important;
  box-shadow: 0 10px 18px rgba(216, 11, 53, .22) !important;
}}

.select-wrapper {{
  width: 100% !important;
  position: relative !important;
}}

.select-icon {{
  left: 17px !important;
  top: 50% !important;
  transform: translateY(-50%) !important;
  font-size: 18px !important;
  z-index: 2 !important;
}}

.styled-select,
.compact-select,
.compact-input {{
  width: 100% !important;
  height: 52px !important;
  min-width: 0 !important;
  border-radius: 15px !important;
  border: 1.5px solid var(--rc-border-strong) !important;
  background-color: #fff !important;
  color: #334155 !important;
  font-size: 16px !important;
  font-weight: 800 !important;
  box-shadow: 0 1px 0 rgba(255,255,255,.8), 0 2px 7px rgba(15,23,42,.035) !important;
}}

.styled-select {{
  padding: 0 42px 0 48px !important;
}}

.compact-select {{
  padding: 0 38px 0 15px !important;
}}

.compact-input {{
  padding: 0 15px !important;
}}

.styled-select:focus,
.compact-select:focus,
.compact-input:focus {{
  border-color: rgba(15, 159, 144, .70) !important;
  box-shadow: 0 0 0 4px rgba(15, 159, 144, .12) !important;
}}

.styled-select.text-red {{
  color: var(--rc-red) !important;
  border-color: rgba(216, 11, 53, .28) !important;
  background-color: #fffafb !important;
}}

/* Controlli avanzati: diventano mini-card ordinate */
.row-3 {{
  display: grid !important;
  grid-template-columns: 1.15fr 1.35fr 1fr auto !important;
  gap: 14px !important;
  align-items: stretch !important;
  flex-wrap: initial !important;
  padding-top: 0 !important;
}}

.adv-group {{
  min-width: 0 !important;
  padding: 15px !important;
  border-radius: 18px !important;
  background: #f8fafc !important;
  border: 1px solid #edf1f5 !important;
  display: flex !important;
  flex-direction: column !important;
  justify-content: space-between !important;
  gap: 11px !important;
}}

.toggle-group {{
  justify-content: center !important;
}}

.toggle-wrap {{
  width: fit-content !important;
  gap: 0 !important;
}}

.toggle-switch {{
  width: 52px !important;
  height: 30px !important;
  background: #cbd5e1 !important;
  border: 1px solid rgba(148,163,184,.35) !important;
  box-shadow: inset 0 1px 3px rgba(15,23,42,.12) !important;
}}

.toggle-switch::after {{
  top: 2px !important;
  left: 2px !important;
  width: 24px !important;
  height: 24px !important;
}}

.toggle-wrap input:checked + .toggle-switch {{
  background: var(--rc-teal) !important;
}}

.toggle-wrap input:checked + .toggle-switch::after {{
  transform: translateX(22px) !important;
}}

.top-group > div {{
  width: 100% !important;
  display: block !important;
}}

.cal-shortcut-btn {{
  display: none !important;
}}

.results-count-wrap {{
  min-width: 120px !important;
  margin-left: 0 !important;
  padding: 15px !important;
  border-radius: 18px !important;
  background: rgba(15,159,144,.08) !important;
  border: 1px solid rgba(15,159,144,.16) !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}}

.results-count {{
  color: var(--rc-teal-dark) !important;
  font-size: 13px !important;
  font-weight: 900 !important;
  text-align: center !important;
  line-height: 1.25 !important;
}}

/* =========================================================
   CLASSIFICA DESKTOP
   ========================================================= */

.table-wrap {{
  width: min(1124px, calc(100% - 56px)) !important;
  margin: 0 auto 46px !important;
  padding: 0 !important;
  overflow: visible !important;
}}

table {{
  width: 100% !important;
  border-collapse: separate !important;
  border-spacing: 0 !important;
  background: #fff !important;
  border-radius: 22px !important;
  overflow: hidden !important;
  box-shadow: var(--rc-shadow) !important;
  border: 1px solid rgba(226,232,240,.90) !important;
}}

thead tr {{
  background: linear-gradient(135deg, #071124, #111b31) !important;
}}

thead th {{
  height: 62px !important;
  padding: 18px 22px !important;
  color: #fff !important;
  font-size: 14px !important;
  font-weight: 900 !important;
  letter-spacing: .08em !important;
  text-transform: uppercase !important;
  border-right: 1px solid rgba(255,255,255,.06) !important;
}}

thead th:last-child {{
  border-right: 0 !important;
}}

tbody tr {{
  background: #fff !important;
  border-bottom: 1px solid var(--rc-border) !important;
  transition: background .18s ease, transform .18s ease, box-shadow .18s ease !important;
}}

tbody tr:hover {{
  background: #fbfdff !important;
}}

tbody tr:last-child {{
  border-bottom: 0 !important;
}}

td {{
  padding: 18px 22px !important;
  vertical-align: middle !important;
}}

.pos-cell {{
  width: 112px !important;
  text-align: left !important;
  padding-right: 12px !important;
}}

.pos-cell > div {{
  justify-content: flex-start !important;
  gap: 12px !important;
}}

.pos-badge {{
  width: 48px !important;
  height: 48px !important;
  font-size: 18px !important;
  font-weight: 950 !important;
  box-shadow: 0 6px 14px rgba(15,23,42,.12) !important;
}}

.pos-1 {{
  background: linear-gradient(145deg, #ffd84a, #ffb800) !important;
  color: #5d4200 !important;
}}

.pos-2 {{
  background: linear-gradient(145deg, #e5e7eb, #b8c0cc) !important;
  color: #334155 !important;
}}

.pos-3 {{
  background: linear-gradient(145deg, #df8a42, #b85e20) !important;
  color: #fff !important;
}}

.pos-top10,
.pos-rest {{
  background: #eef2f7 !important;
  color: #475569 !important;
}}

.trend {{
  border-radius: 999px !important;
  padding: 5px 8px !important;
  font-size: 11px !important;
  font-weight: 900 !important;
}}

td:nth-child(2) {{
  min-width: 0 !important;
}}

.song-artist {{
  color: #0f172a !important;
  font-size: 18px !important;
  line-height: 1.16 !important;
  font-weight: 950 !important;
  letter-spacing: -.25px !important;
  display: flex !important;
  align-items: center !important;
  gap: 10px !important;
}}

.song-artist > span {{
  min-width: 0 !important;
}}

.song-title {{
  margin-top: 7px !important;
  color: #64748b !important;
  font-size: 15px !important;
  font-weight: 550 !important;
}}

.song-year {{
  margin-left: 9px !important;
  padding: 5px 11px !important;
  border-radius: 10px !important;
  background: #eef2ff !important;
  border: 1px solid #dbe3ff !important;
  color: #3446b4 !important;
  font-size: 13px !important;
  font-weight: 900 !important;
}}

.play-btn {{
  width: 42px !important;
  height: 42px !important;
  border-radius: 999px !important;
  background: linear-gradient(145deg, var(--rc-red), var(--rc-red-dark)) !important;
  color: #fff !important;
  font-size: 16px !important;
  box-shadow: 0 9px 18px rgba(216, 11, 53, .22) !important;
  flex: 0 0 auto !important;
}}

.play-btn:hover {{
  transform: translateY(-1px) scale(1.04) !important;
  box-shadow: 0 12px 22px rgba(216, 11, 53, .30) !important;
}}

.radio-date-cell {{
  width: 170px !important;
  text-align: center !important;
}}

.radio-date-badge {{
  min-width: 128px !important;
  justify-content: center !important;
  padding: 11px 13px !important;
  border-radius: 14px !important;
  background: rgba(15, 159, 144, .08) !important;
  border: 1px solid rgba(15, 159, 144, .16) !important;
  color: #0f8d81 !important;
  font-size: 15px !important;
  font-weight: 900 !important;
}}

.plays-cell {{
  width: 150px !important;
  text-align: right !important;
}}

.plays-num {{
  color: var(--rc-red) !important;
  font-size: 25px !important;
  line-height: 1 !important;
  font-weight: 950 !important;
  letter-spacing: -.4px !important;
}}

.plays-lbl {{
  margin-top: 5px !important;
  color: #64748b !important;
  font-size: 11px !important;
  font-weight: 800 !important;
  letter-spacing: .04em !important;
}}

/* =========================================================
   TABLET
   ========================================================= */

@media (max-width: 980px) {{
  .filter-grid {{
    grid-template-columns: 1fr 1fr !important;
  }}

  .decennio-section {{
    grid-column: 1 / -1 !important;
  }}

  .decade-chips {{
    grid-template-columns: repeat(5, minmax(0, 1fr)) !important;
  }}

  .row-3 {{
    grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
  }}

  .results-count-wrap {{
    grid-column: 1 / -1 !important;
    min-height: 52px !important;
  }}
}}

/* =========================================================
   MOBILE - layout verticale vero, niente colonne rotte
   ========================================================= */

@media (max-width: 768px) {{
  body {{
    background: #f4f7fb !important;
  }}

  .header-top {{
    padding: 18px 16px 16px !important;
    align-items: flex-start !important;
  }}

  .logo-icon {{
    width: 48px !important;
    height: 48px !important;
    border-radius: 15px !important;
    font-size: 22px !important;
  }}

  .logo-text h1 {{
    font-size: 27px !important;
  }}

  .logo-text span {{
    margin-top: 7px !important;
    font-size: 12px !important;
    letter-spacing: .20em !important;
  }}

  .header-meta {{
    min-width: 112px !important;
    font-size: 12px !important;
  }}

  .header-meta strong {{
    font-size: 16px !important;
    line-height: 1.12 !important;
  }}

  #user-badge {{
    padding: 6px 9px !important;
    font-size: 11px !important;
    gap: 6px !important;
  }}

  .radio-tabs {{
    padding: 0 12px !important;
  }}

  .radio-tab {{
    padding: 14px 16px 16px !important;
    font-size: 13px !important;
  }}

  .radio-tab.active::after,
  .radio-tab.globale.active::after {{
    left: 12px !important;
    right: 12px !important;
    height: 4px !important;
  }}

  .global-selector-bar {{
    width: auto !important;
    margin: 14px 10px 0 !important;
    padding: 0 !important;
  }}

  .global-selector-header {{
    min-height: 54px !important;
    padding: 12px 14px !important;
    border-radius: 17px !important;
  }}

  .global-selector-summary {{
    font-size: 15px !important;
  }}

  .global-toggle-btn {{
    font-size: 12px !important;
    padding: 7px 9px !important;
  }}

  .global-selector-body.open {{
    padding: 14px !important;
    gap: 12px !important;
  }}

  .global-checkboxes-container,
  .global-checkboxes {{
    width: 100% !important;
  }}

  .global-cb-wrap {{
    font-size: 12px !important;
    padding: 7px 10px !important;
  }}

  .filters-bar {{
    width: auto !important;
    margin: 16px 10px 18px !important;
    padding: 15px !important;
    border-radius: 22px !important;
    gap: 16px !important;
    box-shadow: 0 12px 30px rgba(15, 23, 42, .09) !important;
  }}

  .row-1 {{
    grid-template-columns: 1fr !important;
    gap: 12px !important;
  }}

  .search-box input {{
    height: 54px !important;
    border-radius: 16px !important;
    font-size: 16px !important;
    padding-left: 18px !important;
    padding-right: 50px !important;
  }}

  .search-box .icon {{
    right: 17px !important;
    font-size: 20px !important;
  }}

  .export-btn,
  #export-btn {{
    height: 52px !important;
    border-radius: 16px !important;
    font-size: 16px !important;
  }}

  .filter-grid {{
    grid-template-columns: 1fr 1fr !important;
    gap: 15px !important;
    padding: 16px 0 !important;
  }}

  .decennio-section {{
    grid-column: 1 / -1 !important;
  }}

  .filter-section {{
    gap: 10px !important;
  }}

  .filter-label {{
    font-size: 12px !important;
    letter-spacing: .075em !important;
  }}

  .decade-chips {{
    grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
    gap: 8px !important;
  }}

  .chip {{
    height: 38px !important;
    padding: 0 8px !important;
    font-size: 14px !important;
  }}

  .styled-select,
  .compact-select,
  .compact-input {{
    height: 48px !important;
    border-radius: 14px !important;
    font-size: 14px !important;
  }}

  .styled-select {{
    padding-left: 40px !important;
    padding-right: 34px !important;
  }}

  .select-icon {{
    left: 14px !important;
    font-size: 16px !important;
  }}

  .row-3 {{
    grid-template-columns: 1fr 1fr !important;
    gap: 10px !important;
  }}

  .adv-group {{
    padding: 12px !important;
    border-radius: 16px !important;
    gap: 9px !important;
  }}

  .toggle-group {{
    grid-column: 1 / -1 !important;
    min-height: 76px !important;
  }}

  .toggle-group .toggle-wrap {{
    margin-top: 2px !important;
  }}

  .toggle-switch {{
    width: 48px !important;
    height: 28px !important;
  }}

  .toggle-switch::after {{
    width: 22px !important;
    height: 22px !important;
  }}

  .toggle-wrap input:checked + .toggle-switch::after {{
    transform: translateX(20px) !important;
  }}

  .results-count-wrap {{
    grid-column: 1 / -1 !important;
    min-height: 48px !important;
    padding: 12px !important;
  }}

  .results-count {{
    font-size: 12px !important;
  }}

  /* Mobile classifica: trasformo la tabella in card verticali */
  .table-wrap {{
    width: auto !important;
    margin: 0 10px 34px !important;
    padding: 0 !important;
    overflow: visible !important;
  }}

  table,
  thead,
  tbody,
  tr,
  td {{
    display: block !important;
  }}

  table {{
    background: transparent !important;
    border: 0 !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    overflow: visible !important;
  }}

  thead {{
    display: none !important;
  }}

  tbody {{
    display: flex !important;
    flex-direction: column !important;
    gap: 10px !important;
  }}

  tbody tr {{
    display: grid !important;
    grid-template-columns: 68px minmax(0, 1fr) auto !important;
    grid-template-areas:
      "pos song plays"
      "pos date date" !important;
    gap: 8px 12px !important;
    padding: 14px !important;
    border: 1px solid rgba(226,232,240,.94) !important;
    border-radius: 19px !important;
    background: #fff !important;
    box-shadow: 0 8px 22px rgba(15,23,42,.065) !important;
  }}

  tbody tr.top1 {{
    background: linear-gradient(90deg, rgba(250,204,21,.12), #fff 34%) !important;
  }}

  tbody tr.top2 {{
    background: linear-gradient(90deg, rgba(148,163,184,.12), #fff 34%) !important;
  }}

  tbody tr.top3 {{
    background: linear-gradient(90deg, rgba(205,127,50,.12), #fff 34%) !important;
  }}

  tbody td {{
    padding: 0 !important;
    width: auto !important;
    min-width: 0 !important;
  }}

  .pos-cell {{
    grid-area: pos !important;
    display: flex !important;
    align-items: flex-start !important;
    justify-content: center !important;
    width: auto !important;
    padding: 0 !important;
  }}

  .pos-cell > div {{
    flex-direction: column !important;
    gap: 8px !important;
    align-items: center !important;
    justify-content: flex-start !important;
  }}

  .pos-cell > div > div:last-child {{
    width: auto !important;
  }}

  .pos-badge {{
    width: 48px !important;
    height: 48px !important;
    font-size: 18px !important;
  }}

  td:nth-child(2) {{
    grid-area: song !important;
    padding: 0 !important;
    padding-right: 0 !important;
    position: relative !important;
  }}

  .song-artist {{
    width: 100% !important;
    display: flex !important;
    align-items: flex-start !important;
    justify-content: space-between !important;
    gap: 10px !important;
    font-size: 17px !important;
    line-height: 1.14 !important;
  }}

  .song-artist > span {{
    display: block !important;
    flex: 1 1 auto !important;
    min-width: 0 !important;
    overflow-wrap: anywhere !important;
  }}

  .song-title {{
    margin-top: 6px !important;
    font-size: 14px !important;
  }}

  .song-year {{
    display: inline-flex !important;
    margin-left: 0 !important;
    margin-top: 7px !important;
    width: fit-content !important;
    padding: 4px 9px !important;
    font-size: 12px !important;
    border-radius: 9px !important;
  }}

  #chart-body .play-btn {{
    width: 38px !important;
    height: 38px !important;
    font-size: 15px !important;
    margin-left: auto !important;
    margin-top: 0 !important;
  }}

  .radio-date-cell {{
    grid-area: date !important;
    text-align: left !important;
    width: auto !important;
    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
  }}

  .radio-date-badge {{
    min-width: 0 !important;
    width: fit-content !important;
    padding: 9px 11px !important;
    border-radius: 12px !important;
    font-size: 13px !important;
  }}

  .plays-cell {{
    grid-area: plays !important;
    width: auto !important;
    min-width: 78px !important;
    text-align: right !important;
    align-self: start !important;
  }}

  .plays-num {{
    font-size: 22px !important;
  }}

  .plays-lbl {{
    font-size: 10px !important;
  }}

  .trend {{
    font-size: 10px !important;
    padding: 4px 7px !important;
  }}
}}

/* =========================================================
   MOBILE MOLTO STRETTO
   ========================================================= */

@media (max-width: 430px) {{
  .header-top {{
    gap: 10px !important;
  }}

  .logo {{
    gap: 9px !important;
  }}

  .logo-icon {{
    width: 42px !important;
    height: 42px !important;
    border-radius: 13px !important;
    font-size: 19px !important;
  }}

  .logo-text h1 {{
    font-size: 23px !important;
  }}

  .logo-text span {{
    font-size: 10px !important;
    letter-spacing: .18em !important;
  }}

  .header-meta {{
    font-size: 11px !important;
    min-width: 100px !important;
  }}

  .header-meta strong {{
    font-size: 14px !important;
  }}

  #user-badge span {{
    max-width: 78px !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    white-space: nowrap !important;
  }}

  .decade-chips {{
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
  }}

  .filter-grid {{
    grid-template-columns: 1fr !important;
  }}

  .data-section,
  .orario-section {{
    grid-column: auto !important;
  }}

  .row-3 {{
    grid-template-columns: 1fr !important;
  }}

  .toggle-group,
  .results-count-wrap {{
    grid-column: auto !important;
  }}

  tbody tr {{
    grid-template-columns: 52px minmax(0, 1fr) !important;
    grid-template-areas:
      "pos song"
      "pos plays"
      "pos date" !important;
  }}

  .plays-cell {{
    text-align: left !important;
    display: flex !important;
    align-items: baseline !important;
    gap: 6px !important;
  }}

  .plays-lbl {{
    margin-top: 0 !important;
  }}
}}

  .date-panel.open {{ display: block !important; }}
  .hour-panel.open {{ display: block !important; }}
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
    <button class="radio-tab globale active" id="tab-globale" onclick="switchRadio('globale')">🌍 Classifica Globale</button>
    <button class="radio-tab" onclick="switchRadio('subasio')">Radio Subasio</button>
    <button class="radio-tab" onclick="switchRadio('divina')">Radio Divina</button>
    <button class="radio-tab" onclick="switchRadio('mitology')">Radio Mitology</button>
    <button class="radio-tab" onclick="switchRadio('nostalgia')">Nostalgia Toscana</button>
    <button class="radio-tab" onclick="switchRadio('toscana')">Radio Toscana</button>
    <button class="radio-tab" onclick="switchRadio('italia')">Radio Italia</button>
    <button class="radio-tab" onclick="switchRadio('rds')">RDS</button>
    <button class="radio-tab" onclick="switchRadio('rtl1025')">RTL 102.5</button>
    <button class="radio-tab" onclick="switchRadio('birikina')">Radio Birikina</button>
    <button class="radio-tab" onclick="switchRadio('bruno')">Radio Bruno</button>
    <button class="radio-tab" onclick="switchRadio('kisskiss')">Radio Kiss Kiss</button>
    <button class="radio-tab" onclick="switchRadio('m2o')">Radio m2o</button>
    <button class="radio-tab" onclick="switchRadio('propostaaosta')">Proposta Aosta</button>
    <button class="radio-tab" onclick="switchRadio('capital')">Radio Capital</button>
  </div>
</header>

<div class="global-selector-bar" id="global-selector-bar">
  <div class="global-selector-header" onclick="toggleGlobalSelectorBody()">
    <span class="global-selector-summary">🌍 Canali sommati: <strong id="global-active-count">Caricamento...</strong></span>
    <button class="global-toggle-btn" id="global-toggle-btn" onclick="event.stopPropagation(); toggleGlobalSelectorBody()">Personalizza ▾</button>
  </div>
  <div class="global-selector-body" id="global-selector-body">
    <div class="global-checkboxes-container">
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
        <label class="global-cb-wrap checked" id="cb-birikina">
          <input type="checkbox" checked onchange="toggleGlobalRadio('birikina')" data-radio="birikina">
          <span class="global-cb-check"></span>
          <span class="global-cb-label">Birikina</span>
        </label>
        <label class="global-cb-wrap checked" id="cb-bruno">
          <input type="checkbox" checked onchange="toggleGlobalRadio('bruno')" data-radio="bruno">
          <span class="global-cb-check"></span>
          <span class="global-cb-label">Bruno</span>
        </label>
        <label class="global-cb-wrap checked" id="cb-kisskiss">
          <input type="checkbox" checked onchange="toggleGlobalRadio('kisskiss')" data-radio="kisskiss">
          <span class="global-cb-check"></span>
          <span class="global-cb-label">Kiss Kiss</span>
        </label>
        <label class="global-cb-wrap checked" id="cb-m2o">
          <input type="checkbox" checked onchange="toggleGlobalRadio('m2o')" data-radio="m2o">
          <span class="global-cb-check"></span>
          <span class="global-cb-label">m2o</span>
        </label>
        <label class="global-cb-wrap checked" id="cb-propostaaosta">
          <input type="checkbox" checked onchange="toggleGlobalRadio('propostaaosta')" data-radio="propostaaosta">
          <span class="global-cb-check"></span>
          <span class="global-cb-label">Proposta</span>
        </label>
        <label class="global-cb-wrap checked" id="cb-capital">
          <input type="checkbox" checked onchange="toggleGlobalRadio('capital')" data-radio="capital">
          <span class="global-cb-check"></span>
          <span class="global-cb-label">Capital</span>
        </label>
      </div>
    </div>
    <div class="global-actions">
      <button class="global-action-btn" onclick="selectAllGlobal()">✓ Tutte</button>
      <button class="global-action-btn" onclick="selectNoneGlobal()">✕ Nessuna</button>
    </div>
  </div>
</div>

<div class="filters-bar">
  <!-- Riga 1: Cerca + Esporta + Confronto -->
  <div class="filter-row row-1">
    <div class="search-box">
      <input type="text" id="search-input" placeholder="Cerca artista o titolo…" oninput="applyFilters()">
      <span class="icon">🔍</span>
    </div>
    <button class="compare-btn" id="compare-btn" onclick="openCompareModal()" title="Confronta ed evidenzia brani mancanti" style="display: inline-flex; align-items: center; justify-content: center; gap: 6px; background: #4f46e5; color: #fff; border: none; border-radius: 8px; padding: 10px 16px; font-size: 13px; font-weight: 700; cursor: pointer; transition: all 0.2s ease; box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25);">
      📊 Confronto Playlist
    </button>
    <button class="export-btn" id="export-btn" onclick="exportToCSV()" title="Esporta classifica filtrata in CSV" style="display: inline-flex; align-items: center; justify-content: center; gap: 6px; background: #0d9488; color: #fff; border: none; border-radius: 8px; padding: 10px 16px; font-size: 13px; font-weight: 700; cursor: pointer; transition: all 0.2s ease; box-shadow: 0 4px 12px rgba(13, 148, 136, 0.25);">
      <svg class="export-icon" viewBox="0 0 24 24" style="width: 16px; height: 16px; fill: currentColor;"><path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96zM17 13l-5 5-5-5h3V9h4v4h3z"/></svg>
      Esporta CSV
    </button>
  </div>

  <div class="filter-grid">
    <!-- Decennio Section -->
    <div class="filter-section decennio-section">
      <span class="filter-label">DECENNIO</span>
      <div class="decade-chips" id="decade-chips"></div>
    </div>
    
    <!-- Data Section -->
    <div class="filter-section data-section">
      <span class="filter-label">DATA</span>
      <div class="date-filter-wrap" style="position: relative; width: 100%;">
        <div class="select-wrapper">
          <span class="select-icon" style="color: var(--red);">📅</span>
          <select id="date-select" class="styled-select text-red" onchange="onDateSelectChange(this.value)">
            <option value="30">30 giorni</option>
            <option value="7">7 giorni</option>
            <option value="90">90 giorni</option>
            <option value="all">Tutto</option>
            <option value="custom">Scegli dal calendario...</option>
          </select>
        </div>
        <div class="date-panel" id="date-panel" style="display:none; position:absolute; top:calc(100% + 6px); left:0; z-index:200; background:#fff; border:1.5px solid var(--rc-border); border-radius:12px; box-shadow:var(--rc-shadow); padding:14px; min-width:260px;">
          <div class="cal-shortcuts" style="display: flex; gap: 4px; flex-wrap: wrap; margin-bottom: 10px;">
            <button class="cal-shortcut-btn" id="preset-all"       onclick="selectPreset('all')" style="padding: 4px 8px; font-size: 11px; border-radius: 6px; border: 1px solid var(--rc-border-strong); background: #f8fafc; font-weight: 700; cursor: pointer;">Tutte</button>
            <button class="cal-shortcut-btn" id="preset-7"         onclick="selectPreset(7)" style="padding: 4px 8px; font-size: 11px; border-radius: 6px; border: 1px solid var(--rc-border-strong); background: #f8fafc; font-weight: 700; cursor: pointer;">7 gg</button>
            <button class="cal-shortcut-btn" id="preset-30"        onclick="selectPreset(30)" style="padding: 4px 8px; font-size: 11px; border-radius: 6px; border: 1px solid var(--rc-border-strong); background: #f8fafc; font-weight: 700; cursor: pointer;">Mese</button>
          </div>
          <div class="cal-nav" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <button class="cal-nav-btn" onclick="calShiftMonth(-1)" style="background: none; border: none; font-size: 18px; cursor: pointer; font-weight: bold;">&#8249;</button>
            <span class="cal-month-label" id="cal-month-label" style="font-weight: 800; font-size: 14px;"></span>
            <button class="cal-nav-btn" onclick="calShiftMonth(1)" style="background: none; border: none; font-size: 18px; cursor: pointer; font-weight: bold;">&#8250;</button>
          </div>
          <div class="cal-grid" id="cal-grid" style="display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; text-align: center; font-size: 12px;">
            <div class="cal-head" style="font-weight: 800; color: var(--rc-muted);">Lu</div>
            <div class="cal-head" style="font-weight: 800; color: var(--rc-muted);">Ma</div>
            <div class="cal-head" style="font-weight: 800; color: var(--rc-muted);">Me</div>
            <div class="cal-head" style="font-weight: 800; color: var(--rc-muted);">Gi</div>
            <div class="cal-head" style="font-weight: 800; color: var(--rc-muted);">Ve</div>
            <div class="cal-head" style="font-weight: 800; color: var(--rc-muted);">Sa</div>
            <div class="cal-head" style="font-weight: 800; color: var(--rc-muted);">Do</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Orario Section -->
    <div class="filter-section orario-section">
      <span class="filter-label">ORARIO</span>
      <div class="hour-filter-wrap" style="position: relative; width: 100%;">
        <div class="select-wrapper">
          <span class="select-icon">🕒</span>
          <select id="hour-select" class="styled-select" onchange="onHourSelectChange(this.value)">
            <option value="all">Tutto</option>
            <option value="mattina">Mattina</option>
            <option value="pomeriggio">Pomeriggio</option>
            <option value="sera">Sera</option>
            <option value="notte">Notte</option>
            <option value="custom">Scegli ore...</option>
          </select>
        </div>
        <div class="hour-panel" id="hour-panel" style="display:none; position:absolute; top:calc(100% + 6px); left:0; z-index:200; background:#fff; border:1.5px solid var(--rc-border); border-radius:12px; box-shadow:var(--rc-shadow); padding:14px; min-width:320px;">
          <div class="cal-shortcuts" style="display: flex; gap: 4px; flex-wrap: wrap; margin-bottom: 10px;">
            <button class="cal-shortcut-btn" id="hour-preset-all"   onclick="selectHourPreset('all')" style="padding: 4px 8px; font-size: 11px; border-radius: 6px; border: 1px solid var(--rc-border-strong); background: #f8fafc; font-weight: 700; cursor: pointer;">Tutto</button>
            <button class="cal-shortcut-btn" id="hour-preset-none"  onclick="selectHourPreset('none')" style="padding: 4px 8px; font-size: 11px; border-radius: 6px; border: 1px solid var(--rc-border-strong); background: #f8fafc; font-weight: 700; cursor: pointer;">Nessuno</button>
          </div>
          <div class="hour-grid" id="hour-grid" style="display:grid; grid-template-columns:repeat(6,1fr); gap:6px; margin-top:10px;"></div>
        </div>
      </div>
    </div>
  </div>

  <!-- Riga 3: Controlli Avanzati -->
  <div class="filter-row row-3">
    <div class="adv-group toggle-group">
      <span class="filter-label">POSIZIONE ORIGINALE <span class="info-tooltip" title="Mantieni la posizione originale del brano in classifica anche quando filtri per nome">ⓘ</span></span>
      <label class="toggle-wrap">
        <input type="checkbox" id="keep-rank-checkbox" onchange="applyFilters()">
        <span class="toggle-switch"></span>
      </label>
    </div>

    <div class="adv-group top-group" style="flex-direction: row !important; align-items: center !important; gap: 8px !important; justify-content: center !important;">
      <span style="font-size: 13px; font-weight: 900; color: #475569; text-transform: uppercase; letter-spacing: .09em; white-space: nowrap;">PRIME</span>
      <input type="number" id="top-input" min="1" value="50" class="compact-input" style="width: 80px !important; text-align: center !important; height: 38px !important; padding: 0 !important; font-weight: 800 !important;" oninput="applyFilters()">
      <span style="font-size: 13px; font-weight: 900; color: #475569; text-transform: uppercase; letter-spacing: .09em; white-space: nowrap;">POSIZIONI</span>
      <button id="btn-show-all-positions" onclick="showAllPositions()" style="padding:6px 12px; font-size:12px; font-weight:700; border-radius:8px; border:1.5px solid var(--rc-border-strong); background:#f8fafc; cursor:pointer; margin-left: 8px; transition: all 0.2s; height: 38px;">Tutte</button>
    </div>

    <div class="adv-group min-plays-group">
      <span class="filter-label">MIN PASSAGGI</span>
      <input type="number" class="filter-input compact-input" id="min-plays-input" min="1" placeholder="1" oninput="applyFilters()">
    </div>

    <div class="results-count-wrap">
      <span class="results-count" id="results-count"></span>
    </div>
  </div>
</div>

<!-- Banner Confronto Playlist -->
<div id="compare-active-banner" style="display:none; align-items:center; justify-content:space-between; background:rgba(79, 70, 229, 0.08); border:1.5px dashed #4f46e5; border-radius:12px; padding:12px 18px; margin-bottom:16px; font-size:13.5px; font-weight:700; color:#4f46e5; gap: 12px; flex-wrap: wrap;">
  <span style="display: flex; align-items: center; gap: 8px;">🔍 <span>Confronto Playlist Attivo: vengono mostrati solo i brani dell'export non presenti in <strong><span id="compare-banner-radio-name">...</span></strong></span></span>
  <button onclick="clearPlaylistComparison()" style="background:#4f46e5; color:#fff; border:none; border-radius:8px; padding:6px 12px; font-size:12px; font-weight:700; cursor:pointer; transition: all 0.2s; box-shadow: 0 2px 6px rgba(79,70,229,0.3);">Disattiva Filtro</button>
</div>

<div class="table-wrap">
  <table>
    <thead>
      <tr>
        <th onclick="sortBy('plays', event)" style="width:110px;cursor:pointer" title="Ordina per posizione / passaggi">#</th>
        <th onclick="sortBy('artist', event)" title="Maiusc+Clic per ordinamenti multipli">Artista / Titolo</th>
        <th onclick="sortBy('radioDate', event)" style="text-align:center;width:120px" title="Maiusc+Clic per ordinamenti multipli">Radio Date</th>
        <th class="sorted-desc" onclick="sortBy('plays', event)" style="text-align:right;width:130px" title="Maiusc+Clic per ordinamenti multipli">Passaggi</th>
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

<!-- COMPARISON MODAL -->
<div class="modal-overlay" id="compare-modal-overlay" onclick="closeCompareModal(event)">
  <div class="modal edit-modal" id="compare-modal-box" style="max-width: 600px !important;">
    <div class="modal-header">
      <div class="modal-title">
        <div class="edit-modal-title-text">Confronto Playlist</div>
        <div class="edit-modal-subtitle">Trova canzoni non presenti in una determinata radio</div>
      </div>
      <button class="modal-close" onclick="closeCompareModalDirect()">✕</button>
    </div>
    <div class="modal-body edit-modal-body" style="display:flex; flex-direction:column; gap:16px;">
      
      <div>
        <label for="compare-my-radio" class="edit-input-label">La mia radio (Destinazione)</label>
        <div class="select-wrapper">
          <span class="select-icon" style="color: var(--rc-teal);">📻</span>
          <select id="compare-my-radio" class="styled-select" style="padding-left: 44px !important;">
            <option value="subasio">Radio Subasio</option>
            <option value="divina">Radio Divina</option>
            <option value="mitology">Radio Mitology</option>
            <option value="nostalgia">Nostalgia Toscana</option>
            <option value="toscana">Radio Toscana</option>
            <option value="italia">Radio Italia</option>
            <option value="rds">RDS</option>
            <option value="rtl1025">RTL 102.5</option>
            <option value="birikina">Radio Birikina</option>
            <option value="bruno">Radio Bruno</option>
            <option value="kisskiss">Radio Kiss Kiss</option>
            <option value="m2o">Radio m2o</option>
            <option value="propostaaosta">Proposta Aosta</option>
            <option value="capital">Radio Capital</option>
          </select>
        </div>
      </div>

      <div>
        <label class="edit-input-label">Mando l'export (Seleziona un'altra radio o incolla/carica elenco)</label>
        <div style="display:flex; flex-direction:column; gap:10px;">
          <!-- Opzione 1: Altra radio -->
          <div class="select-wrapper">
            <span class="select-icon" style="color: var(--rc-red);">📻</span>
            <select id="compare-source-radio" class="styled-select" style="padding-left: 44px !important;" onchange="document.getElementById('compare-source-text').value = ''; document.getElementById('compare-source-file').value = '';">
              <option value="">-- Seleziona un'altra radio del database --</option>
              <option value="subasio">Radio Subasio</option>
              <option value="divina">Radio Divina</option>
              <option value="mitology">Radio Mitology</option>
              <option value="nostalgia">Nostalgia Toscana</option>
              <option value="toscana">Radio Toscana</option>
              <option value="italia">Radio Italia</option>
              <option value="rds">RDS</option>
              <option value="rtl1025">RTL 102.5</option>
              <option value="birikina">Radio Birikina</option>
              <option value="bruno">Radio Bruno</option>
              <option value="kisskiss">Radio Kiss Kiss</option>
              <option value="m2o">Radio m2o</option>
              <option value="propostaaosta">Proposta Aosta</option>
              <option value="capital">Radio Capital</option>
            </select>
          </div>

          <div style="text-align: center; font-weight: 700; color: var(--rc-muted); font-size: 12px; margin: 4px 0;">OPPURE INCOLLA/CARICA</div>

          <!-- Opzione 2: Carica File o Incolla testo -->
          <textarea id="compare-source-text" placeholder="Incolla qui l'elenco dei brani (es. Artista - Titolo, uno per riga, o CSV)..." class="edit-year-input-field" style="height:120px; font-family:monospace; font-size:12px; padding:10px; resize:vertical;" oninput="document.getElementById('compare-source-radio').value = '';"></textarea>
          
          <div style="display:flex; align-items:center; gap:8px;">
            <span style="font-size:12px; font-weight:700; color:var(--rc-muted);">Carica file CSV:</span>
            <input type="file" id="compare-source-file" accept=".csv,.txt" style="font-size:12px;" onchange="document.getElementById('compare-source-radio').value = '';">
          </div>
        </div>
      </div>

      <div class="edit-modal-actions" style="margin-top: 10px;">
        <button class="edit-btn edit-btn-cancel" onclick="closeCompareModalDirect()">Chiudi</button>
        <button class="edit-btn edit-btn-save" onclick="runPlaylistComparison()" style="background: linear-gradient(145deg, var(--rc-teal), var(--rc-teal-dark)) !important;">
          <span class="btn-text">Esegui Confronto</span>
        </button>
      </div>

      <!-- Risultati del confronto -->
      <div id="compare-results-area" style="display:none; border-top:1px solid var(--rc-border); padding-top:16px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
          <div style="font-weight:900; color:var(--rc-text); font-size:14px;" id="compare-results-title"></div>
          <button class="cal-shortcut-btn" id="compare-export-csv" onclick="exportCompareResultsToCSV()" style="padding:6px 12px; font-size:11px; background:#0d9488; color:#fff; font-weight:700; border-radius:6px; cursor:pointer; display:inline-block;">Esporta Risultati</button>
        </div>
        <div id="compare-results-table-wrap" style="max-height: 250px; overflow-y: auto; border: 1px solid var(--rc-border); border-radius: 8px; background: #fafafa;">
          <table style="width:100%; border-collapse:collapse; font-size:12px; box-shadow:none; border:none; border-radius:0;">
            <thead style="position:sticky; top:0; background: #071124; z-index:10;">
              <tr>
                <th style="padding:8px 10px; color:#fff; text-align:left; font-size:11px; height:auto; border-right:none;">Artista</th>
                <th style="padding:8px 10px; color:#fff; text-align:left; font-size:11px; height:auto; border-right:none;">Titolo</th>
              </tr>
            </thead>
            <tbody id="compare-results-tbody">
              <!-- Righe generate js -->
            </tbody>
          </table>
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
  rtl1025:{json_rtl1025},
  birikina:{json_birikina},
  bruno:{json_bruno},
  kisskiss:{json_kisskiss},
  m2o:{json_m2o},
  propostaaosta:{json_propostaaosta},
  capital:{json_capital}
}};

let currentRadio = 'globale';
let allSongs = [];
let allDates = [];
let selectedDates = null;  // null = tutte le date; Set = date selezionate
let currentSort = [{{col:'plays', dir:'desc'}}];
let activeDecade = 'all';
let comparisonMissingKeys = null;
let comparisonDestinationRadio = null;

const RADIO_KEYS = ['subasio','divina','mitology','nostalgia','toscana','italia','rds','rtl1025','birikina','bruno','kisskiss','m2o','propostaaosta','capital'];
const RADIO_LABELS = {{
  subasio: 'Radio Subasio', divina: 'Radio Divina', mitology: 'Radio Mitology',
  nostalgia: 'Nostalgia Toscana', toscana: 'Radio Toscana', italia: 'Radio Italia',
  rds: 'RDS', rtl1025: 'RTL 102.5',
  birikina: 'Radio Birikina', bruno: 'Radio Bruno', kisskiss: 'Radio Kiss Kiss',
  m2o: 'Radio m2o', propostaaosta: 'Proposta Aosta', capital: 'Radio Capital'
}};
let globalSelectedRadios = (() => {{
  const saved = localStorage.getItem('radio_charts_global_selected');
  if (saved) {{
    try {{
      const arr = JSON.parse(saved);
      if (Array.isArray(arr) && arr.length > 0) {{
        return new Set(arr.filter(k => RADIO_KEYS.includes(k)));
      }}
    }} catch(e) {{}}
  }}
  return new Set(RADIO_KEYS);
}})();
let isGlobale = true;
let userAllowedRadios = 'all';
let isInitialLoad = true;
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

function applyAllowedRadiosVisibility() {{
  const isAllowed = (radioKey) => {{
    if (userAllowedRadios === 'all' || userAllowedRadios === '*') return true;
    if (Array.isArray(userAllowedRadios)) {{
      return userAllowedRadios.map(r => r.toLowerCase().trim()).includes(radioKey.toLowerCase().trim());
    }}
    return false;
  }};

  RADIO_KEYS.forEach(radioKey => {{
    const allowed = isAllowed(radioKey);
    
    // 1. Pulisci i dati RAW in locale per impedire l'ispezione della cache HTML se non consentito
    if (!allowed) {{
      RAW[radioKey] = {{ songs: [], dates: [] }};
      globalSelectedRadios.delete(radioKey);
      
      // Assicura che la checkbox globale sia deselezionata
      const cbWrap = document.getElementById('cb-' + radioKey);
      if (cbWrap) {{
        cbWrap.classList.remove('checked');
        const input = cbWrap.querySelector('input[type="checkbox"]');
        if (input) input.checked = false;
      }}
    }}
    
    // 2. Mostra/Nascondi la tab corrispondente
    document.querySelectorAll('.radio-tab').forEach(btn => {{
      const onclickAttr = btn.getAttribute('onclick');
      if (onclickAttr && onclickAttr.includes("'" + radioKey + "'")) {{
        btn.style.display = allowed ? '' : 'none';
      }}
    }});

    // 3. Mostra/Nascondi la checkbox nella barra globale
    const cbWrap = document.getElementById('cb-' + radioKey);
    if (cbWrap) {{
      cbWrap.style.display = allowed ? '' : 'none';
    }}
  }});

  // Se la radio selezionata corrente non è più autorizzata, la reimposta a 'globale'
  if (currentRadio !== 'globale' && !isAllowed(currentRadio)) {{
    currentRadio = 'globale';
    isGlobale = true;
  }}
  updateGlobalSelectorSummary();
}}

function toggleGlobalSelectorBody() {{
  const body = document.getElementById('global-selector-body');
  const btn = document.getElementById('global-toggle-btn');
  if (body) {{
    const isOpen = body.classList.toggle('open');
    if (btn) {{
      btn.textContent = isOpen ? 'Chiudi ▴' : 'Personalizza ▾';
    }}
  }}
}}

function updateGlobalSelectorSummary() {{
  const activeCount = globalSelectedRadios.size;
  const activeNames = Array.from(globalSelectedRadios)
    .map(k => RADIO_LABELS[k] ? RADIO_LABELS[k].replace('Radio ', '').replace(' Nostalgia', '') : k)
    .join(', ');
  
  const countEl = document.getElementById('global-active-count');
  if (countEl) {{
    // Conta quante radio hanno dati reali in RAW (cioè sono abilitate per l'utente)
    const totalAllowed = RADIO_KEYS.filter(k => RAW[k] && RAW[k].songs && RAW[k].songs.length > 0).length;
    
    if (activeCount === 0) {{
      countEl.innerHTML = "Nessuna radio selezionata (somma vuota)";
    }} else if (activeCount === totalAllowed) {{
      countEl.innerHTML = activeCount + " radio (tutte)";
    }} else {{
      countEl.innerHTML = activeCount + " radio (" + activeNames + ")";
    }}
  }}
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
    document.getElementById('date-panel')?.classList.remove('open');
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
  
  document.getElementById('date-panel')?.classList.remove('open');
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
  const elSongs = document.getElementById('stat-songs');
  if (elSongs) elSongs.textContent = allSongs.length;
  const elPlays = document.getElementById('stat-plays');
  if (elPlays) elPlays.textContent = totalPlays.toLocaleString('it-IT');
  const elDays = document.getElementById('stat-days');
  if (elDays) elDays.textContent = allDates.length;
  const elTop = document.getElementById('stat-top');
  if (elTop) elTop.textContent = allSongs[0]?.artist || '—';

  buildDecadeChips();
  applyFilters();
}}

function saveGlobalRadiosState() {{
  localStorage.setItem('radio_charts_global_selected', JSON.stringify(Array.from(globalSelectedRadios)));
}}

function applyGlobalCheckboxesState() {{
  RADIO_KEYS.forEach(k => {{
    const wrap = document.getElementById('cb-' + k);
    if (wrap) {{
      const checkbox = wrap.querySelector('input[type="checkbox"]');
      const isChecked = globalSelectedRadios.has(k);
      if (checkbox) checkbox.checked = isChecked;
      if (isChecked) {{
        wrap.classList.add('checked');
      }} else {{
        wrap.classList.remove('checked');
      }}
    }}
  }});
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
  saveGlobalRadiosState();
  
  buildGlobalData();
  updateGlobalSelectorSummary();
  loadData();
}}

function selectAllGlobal() {{
  const isAllowed = (k) => {{
    if (userAllowedRadios === 'all' || userAllowedRadios === '*') return true;
    if (Array.isArray(userAllowedRadios)) {{
      return userAllowedRadios.map(r => r.toLowerCase().trim()).includes(k.toLowerCase().trim());
    }}
    return false;
  }};

  RADIO_KEYS.forEach(radioKey => {{
    if (!isAllowed(radioKey)) return;
    
    globalSelectedRadios.add(radioKey);
    const wrap = document.getElementById(`cb-${{radioKey}}`);
    if (wrap) {{
      wrap.classList.add('checked');
      wrap.querySelector('input[type="checkbox"]').checked = true;
    }}
  }});
  saveGlobalRadiosState();
  buildGlobalData();
  updateGlobalSelectorSummary();
  loadData();
}}

function selectNoneGlobal() {{
  globalSelectedRadios.clear();
  RADIO_KEYS.forEach(radioKey => {{
    const wrap = document.getElementById(`cb-${{radioKey}}`);
    if (wrap) {{
      wrap.classList.remove('checked');
      wrap.querySelector('input[type="checkbox"]').checked = false;
    }}
  }});
  saveGlobalRadiosState();
  buildGlobalData();
  updateGlobalSelectorSummary();
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
    return `<span class="chip${{activeDecade==d?' active':''}}" onclick="filterDecade('${{d}}')">${{label}}</span>`;
  }}).join('');
}}

function filterDecade(d) {{
  activeDecade = d === 'all' ? 'all' : parseInt(d);
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
  document.getElementById('hour-panel')?.classList.toggle('open');
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
  const hourSelect = document.getElementById('hour-select');
  if (hourSelect) {{
    hourSelect.value = selectedHours ? 'custom' : 'all';
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
  }} else if (preset === 'mattina') {{
    selectedHours = new Set([6, 7, 8, 9, 10, 11]);
  }} else if (preset === 'pomeriggio') {{
    selectedHours = new Set([12, 13, 14, 15, 16, 17]);
  }} else if (preset === 'sera') {{
    selectedHours = new Set([18, 19, 20, 21, 22, 23]);
  }} else if (preset === 'notte') {{
    selectedHours = new Set([0, 1, 2, 3, 4, 5]);
  }}
  const select = document.getElementById('hour-select');
  if (select) {{
    select.value = preset;
  }}
  applyFilters();
}}

function toggleDatePanel() {{
  const panel = document.getElementById('date-panel');
  if (panel) panel.classList.toggle('open');
}}

function buildDatePanel() {{
  allDatesSet = new Set(allDates);
  const now = new Date(); now.setHours(0,0,0,0);
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
  const lbl = document.getElementById('cal-month-label');
  const grid = document.getElementById('cal-grid');
  if (!lbl || !grid) return;
  const MONTHS = ['Gennaio','Febbraio','Marzo','Aprile','Maggio','Giugno',
                  'Luglio','Agosto','Settembre','Ottobre','Novembre','Dicembre'];
  lbl.textContent = MONTHS[calMonth] + ' ' + calYear;
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
  const dateSelect = document.getElementById('date-select');
  if (dateSelect) {{
    dateSelect.value = selectedDates ? 'custom' : 'all';
  }}
  updateDateBadge();
  applyFilters();
  buildCalendar();
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

function onDateSelectChange(val) {{
  if (val === 'custom') {{
    buildDatePanel();
    document.getElementById('date-panel')?.classList.add('open');
  }} else {{
    document.getElementById('date-panel')?.classList.remove('open');
    if (val === 'all') {{
      selectPreset('all');
    }} else {{
      selectPreset(parseInt(val));
    }}
  }}
}}

function onHourSelectChange(val) {{
  if (val === 'custom') {{
    buildHourPanel();
    document.getElementById('hour-panel')?.classList.add('open');
  }} else {{
    document.getElementById('hour-panel')?.classList.remove('open');
    selectHourPreset(val);
  }}
}}

function selectPreset(type) {{
  const now = new Date(); now.setHours(0,0,0,0);
  if (type === 'all') {{
    selectedDates = null;
  }} else if (typeof type === 'number') {{
    const cutoff = new Date(now.getTime() - (type-1)*86400000);
    const sel = allDates.filter(d => {{ const dt = ddmmToDate(d); return dt >= cutoff && dt <= now; }});
    selectedDates = new Set(sel);
  }}
  const select = document.getElementById('date-select');
  if (select) {{
    select.value = type.toString();
  }}
  applyFilters();
}}

function updateDateBadge() {{}}

function isSongNew(s) {{
  if (!s.radioDate || s.radioDate === 'N/A' || s.radioDate === 'N/D') return false;
  const parts = s.radioDate.split('/');
  if (parts.length === 3) {{
    const d = parseInt(parts[0]), m = parseInt(parts[1]), y = parseInt(parts[2]);
    const dateVal = new Date(y, m - 1, d);
    const today = new Date();
    today.setHours(0,0,0,0);
    const fourteenDaysAgo = new Date(today.getTime() - 14 * 24 * 60 * 60 * 1000);
    return dateVal >= fourteenDaysAgo;
  }}
  return false;
}}

let visibleCount = 50;

// Chiudi panel cliccando fuori
document.addEventListener('click', e => {{
  const wrap = e.target.closest('.date-filter-wrap');
  if (!wrap) {{
    document.getElementById('date-panel')?.classList.remove('open');
  }}
  const wrapHour = e.target.closest('.hour-filter-wrap');
  if (!wrapHour) {{
    document.getElementById('hour-panel')?.classList.remove('open');
  }}
}});

function showAllPositions() {{
  const input = document.getElementById('top-input');
  if (input) {{
    input.value = '';
    applyFilters();
  }}
}}

function applyFilters() {{
  const q = document.getElementById('search-input').value.toLowerCase().trim();
  
  const topInput = document.getElementById('top-input');
  const topVal = topInput ? topInput.value.trim() : '50';
  const currentLimit = (topVal && parseInt(topVal) > 0) ? parseInt(topVal) : Infinity;
  
  const btnAll = document.getElementById('btn-show-all-positions');
  if (btnAll) {{
    if (!topVal) {{
      btnAll.style.background = '#0d9488';
      btnAll.style.color = '#fff';
      btnAll.style.borderColor = '#0d9488';
    }} else {{
      btnAll.style.background = '#f8fafc';
      btnAll.style.color = 'var(--rc-text)';
      btnAll.style.borderColor = 'var(--rc-border-strong)';
    }}
  }}
  
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

  // 4. Filtra i brani per ricerca, decennio, e posizioni
  let filtered = periodRanked.filter(s => {{
    if(comparisonMissingKeys && !comparisonMissingKeys.has(getNormKey(s.artist, s.title))) return false;
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
  
  const shown = filtered.slice(0, currentLimit);
  
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
    const diff = s.rank - s._periodRank;
    let trendHtml;
    if (isSongNew(s) && diff >= 0) {{
      trendHtml = `<span class="trend trend-new">NEW</span>`;
    }} else if (diff > 0) {{
      trendHtml = `<span class="trend trend-up">+${{diff}}</span>`;
    }} else if (diff < 0) {{
      trendHtml = `<span class="trend trend-down">-${{Math.abs(diff)}}</span>`;
    }} else {{
      trendHtml = `<span class="trend trend-stable">=</span>`;
    }}

    const isNa = s.year === 'N/A';
    const displayYear = isNa ? 'N/D' : s.year;
    const yearClass = isNa ? 'song-year na' : 'song-year';
    const yearBadge = `<span class="${{yearClass}}" title="Modifica anno di pubblicazione" onclick="openEditYearModal(event, ${{i}})">${{displayYear}}<svg viewBox="0 0 24 24" style="width:10px;height:10px;margin-left:4px;fill:currentColor;vertical-align:middle"><path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/></svg></span>`;

    const isRdNa = !s.radioDate || s.radioDate === 'N/A' || s.radioDate === 'N/D';
    const displayRd = isRdNa ? 'N/D' : s.radioDate;
    const rdClass = isRdNa ? 'radio-date-badge na' : 'radio-date-badge';
    const radioDateBadge = `<span class="${{rdClass}}" title="Modifica radio date" onclick="openEditYearModal(event, ${{i}})">⏱ ${{displayRd}}<svg viewBox="0 0 24 24" style="width:10px;height:10px;margin-left:4px;fill:currentColor;vertical-align:middle"><path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/></svg></span>`;

    const playsVal = s._filtTotal !== undefined ? s._filtTotal : s.total;

    return `<tr class="${{rowClass}}">
      <td class="pos-cell" style="padding-right: 0 !important;">
        <div style="display: flex; align-items: center; justify-content: center; gap: 12px;">
          <div class="pos-badge ${{posClass}}">${{pos}}</div>
          <div style="width: 36px; display: flex; justify-content: center; text-align: center;">${{trendHtml}}</div>
        </div>
      </td>
      <td style="position: relative; padding-right: 52px !important;">
        <div class="song-artist" style="display:flex;align-items:center;gap:6px">
          <span>${{esc(s.artist)}}${{yearBadge}}</span>
          <button class="play-btn" title="Ascolta anteprima" onclick="event.stopPropagation();playPreview(renderedSongs[${{i}}].artist,renderedSongs[${{i}}].title,this,renderedSongs[${{i}}].previewUrl)">▶</button>
        </div>
        <div class="song-title">${{esc(s.title)}}</div>
      </td>
      <td class="radio-date-cell">${{radioDateBadge}}</td>
      <td class="plays-cell" onclick="showPopup(${{i}})" title="Clicca per vedere orari di messa in onda">
        <div class="plays-num">${{playsVal}}</div>
        <div class="plays-lbl">${{selectedDates ? 'nei giorni sel.' : 'pass.'}}</div>
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
          return '<div style="display:flex;align-items:center;gap:10px;padding:6px 0;border-bottom:1px solid rgba(0,0,0,0.03);">'
          + '<button class="play-btn" style="width:24px !important;height:24px !important;font-size:10px !important;flex-shrink:0;margin:0 !important;padding:0 !important;display:flex;align-items:center;justify-content:center;" '
          + 'data-artist="' + esc(s.artist) + '" data-title="' + esc(e.title) + '" '
          + (ePrevVal ? 'data-preview="' + esc(ePrevVal) + '" ' : '')
          + 'onclick="event.stopPropagation();playPreviewBtn(this)" title="Ascolta anteprima">▶</button>'
          + (e.time !== 'In diretta' ? '<span class="time-chip" style="margin:0 !important;flex-shrink:0;">' + esc(e.time) + '</span>' : '')
          + '<span style="font-size:13px;color:var(--text);text-align:left;line-height:1.3;'+(e.title===s.title?'font-weight:700;color:var(--red)':'')+'">'
          + esc(e.title) + (e.year!=='N/A' ? ' <span style="font-size:10px;color:var(--text-muted);font-weight:normal;">('+e.year+')</span>' : '')
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
      localStorage.setItem('radio_charts_allowed_radios', JSON.stringify(data.allowedRadios));
      userAllowedRadios = data.allowedRadios;
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
    tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;padding:50px;font-weight:600;color:var(--text-muted)">Caricamento dati in corso... ⏳</td></tr>';
  }}

  try {{
    const dataUrl = `${{APPS_SCRIPT_URL}}?action=getData&username=${{encodeURIComponent(user)}}&password=${{encodeURIComponent(pass)}}`;
    const res = await fetch(dataUrl);
    const result = await res.json();
    
    if (result.success) {{
      localStorage.setItem('radio_charts_allowed_radios', JSON.stringify(result.allowedRadios));
      userAllowedRadios = result.allowedRadios;
      applyAllowedRadiosVisibility();

      Object.keys(result.data).forEach(k => {{
        RAW[k] = result.data[k];
      }});
      userRole = result.role;
      loggedInUser = user;
      
      updateUserHeaderBadge();
      updateEditPermissions();
      if (isInitialLoad) {{
        document.getElementById('top-input').value = '50';
        switchRadio(currentRadio);
        selectPreset(30);
        isInitialLoad = false;
      }} else {{
        switchRadio(currentRadio);
      }}
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
    applyAllowedRadiosVisibility();
    applyGlobalCheckboxesState();
    if (isInitialLoad) {{
      document.getElementById('top-input').value = '50';
      switchRadio(currentRadio);
      selectPreset(30);
      isInitialLoad = false;
    }} else {{
      switchRadio(currentRadio);
    }}
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
  localStorage.removeItem('radio_charts_allowed_radios');
  userAllowedRadios = 'all';
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
    const savedAllowed = localStorage.getItem('radio_charts_allowed_radios');
    if (savedAllowed) {{
      try {{
        userAllowedRadios = JSON.parse(savedAllowed);
      }} catch(e) {{
        userAllowedRadios = 'all';
      }}
    }}
    applyAllowedRadiosVisibility();
    applyGlobalCheckboxesState();
    if (user && pass) {{
      document.getElementById('login-overlay').style.display = 'none';
      fetchChartsData();
    }} else {{
      showLoginScreen();
    }}
  }} else {{
    document.getElementById('login-overlay').style.display = 'none';
    userRole = 'admin'; // offline sono tutti admin
    userAllowedRadios = 'all';
    updateEditPermissions();
    applyAllowedRadiosVisibility();
    applyGlobalCheckboxesState();
    if (isInitialLoad) {{
      document.getElementById('top-input').value = '50';
      switchRadio(currentRadio);
      selectPreset(30);
      isInitialLoad = false;
    }} else {{
      switchRadio(currentRadio);
    }}
  }}

  // Abilita lo scorrimento orizzontale con la rotellina del mouse e con il trascinamento del mouse
  const tabs = document.querySelector('.radio-tabs');
  if (tabs) {{
    tabs.addEventListener('wheel', (e) => {{
      if (e.deltaY !== 0) {{
        e.preventDefault();
        tabs.scrollLeft += e.deltaY;
      }}
    }}, {{ passive: false }});

    let isDown = false;
    let startX;
    let scrollLeft;
    let hasDragged = false;

    tabs.addEventListener('mousedown', (e) => {{
      isDown = true;
      hasDragged = false;
      tabs.classList.add('active-drag');
      startX = e.pageX - tabs.offsetLeft;
      scrollLeft = tabs.scrollLeft;
    }});

    tabs.addEventListener('mousemove', (e) => {{
      if (!isDown) return;
      e.preventDefault();
      const x = e.pageX - tabs.offsetLeft;
      const walk = (x - startX) * 1.5; // velocità di trascinamento
      if (Math.abs(walk) > 5) {{
        hasDragged = true;
      }}
      tabs.scrollLeft = scrollLeft - walk;
    }});

    tabs.addEventListener('mouseup', () => {{
      isDown = false;
      tabs.classList.remove('active-drag');
    }});

    tabs.addEventListener('mouseleave', () => {{
      isDown = false;
      tabs.classList.remove('active-drag');
    }});

    // Blocca il click sui pulsanti radio se c'è stato un trascinamento
    tabs.addEventListener('click', (e) => {{
      if (hasDragged) {{
        e.preventDefault();
        e.stopPropagation();
      }}
    }}, true); // Fase di cattura
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
let lastCompareMissingSongs = [];

function openCompareModal() {{
  document.getElementById('compare-modal-overlay').classList.add('open');
}}

function closeCompareModal(e) {{
  if (e.target.id === 'compare-modal-overlay') {{
    closeCompareModalDirect();
  }}
}}

function closeCompareModalDirect() {{
  document.getElementById('compare-modal-overlay').classList.remove('open');
}}

async function runPlaylistComparison() {{
  const myRadioKey = document.getElementById('compare-my-radio').value;
  const sourceRadioKey = document.getElementById('compare-source-radio').value;
  const sourceText = document.getElementById('compare-source-text').value.trim();
  const fileInput = document.getElementById('compare-source-file');
  
  let sourceSongs = [];
  
  if (sourceRadioKey) {{
    // Confronta con un'altra radio del database
    sourceSongs = RAW[sourceRadioKey].songs;
  }} else if (fileInput.files.length > 0) {{
    // Carica da file
    const file = fileInput.files[0];
    const text = await new Promise((resolve) => {{
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target.result);
      reader.readAsText(file);
    }});
    sourceSongs = parseExportSongs(text);
  }} else if (sourceText) {{
    // Carica da testo incollato
    sourceSongs = parseExportSongs(sourceText);
  }} else {{
    alert("Seleziona una radio di confronto, carica un file CSV o incolla l'elenco dei brani!");
    return;
  }}

  if (sourceSongs.length === 0) {{
    alert("Nessun brano trovato nella sorgente di confronto.");
    return;
  }}

  // Costruisci il Set delle canzoni presenti in "La mia radio" (usando chiave normalizzata)
  const myRadioSongs = RAW[myRadioKey].songs;
  const myRadioSet = new Set(myRadioSongs.map(s => getNormKey(s.artist, s.title)));

  // Trova le canzoni mancanti
  const missingSongs = [];
  const addedKeys = new Set(); // per evitare duplicati nei risultati

  sourceSongs.forEach(s => {{
    const key = getNormKey(s.artist, s.title);
    if (!myRadioSet.has(key) && !addedKeys.has(key)) {{
      addedKeys.add(key);
      missingSongs.push({{ artist: s.artist, title: s.title }});
    }}
  }});

  if (missingSongs.length === 0) {{
    alert("Tutte le canzoni dell'export sono già presenti nella tua radio! 🎉");
    return;
  }}

  // Imposta i filtri globali per il confronto
  comparisonMissingKeys = addedKeys;
  comparisonDestinationRadio = myRadioKey;

  // Mostra il banner in cima alla tabella
  const banner = document.getElementById('compare-active-banner');
  if (banner) {{
    banner.style.display = 'flex';
    document.getElementById('compare-banner-radio-name').textContent = RADIO_LABELS[myRadioKey] || myRadioKey;
  }}

  // Chiudi il modal
  closeCompareModalDirect();

  // Cambia radio attiva sulla pagina principale:
  // Se la sorgente è un'altra radio, mostra quella.
  // Altrimenti, mostra la vista globale.
  if (sourceRadioKey) {{
    switchRadio(sourceRadioKey);
  }} else {{
    switchRadio('globale');
  }}

  // Applica i filtri per visualizzare i brani nella schermata principale
  applyFilters();
}}

function clearPlaylistComparison() {{
  comparisonMissingKeys = null;
  comparisonDestinationRadio = null;
  const banner = document.getElementById('compare-active-banner');
  if (banner) {{
    banner.style.display = 'none';
  }}
  applyFilters();
}}

function parseExportSongs(text) {{
  const songs = [];
  const lines = text.split('\\n');
  lines.forEach(line => {{
    line = line.trim();
    if (!line) return;
    
    // Prova a splittare per csv / tab / semicolon
    let artist = '', title = '';
    if (line.includes(';')) {{
      const parts = line.split(';');
      if (parts.length >= 2) {{
        artist = parts[0].trim();
        title = parts[1].trim();
      }}
    }} else if (line.includes(',')) {{
      const parts = line.split(',');
      if (parts.length >= 2) {{
        artist = parts[0].trim();
        title = parts[1].trim();
      }}
    }} else if (line.includes(' - ')) {{
      const parts = line.split(' - ');
      artist = parts[0].trim();
      title = parts[1].trim();
    }} else if (line.includes(' – ')) {{
      const parts = line.split(' – ');
      artist = parts[0].trim();
      title = parts[1].trim();
    }} else {{
      // Riga singola, considerala come titolo
      title = line;
    }}
    
    // Rimuovi virgolette se presenti
    artist = artist.replace(/^["']|["']$/g, '').trim();
    title = title.replace(/^["']|["']$/g, '').trim();
    
    if (title) {{
      songs.push({{ artist: artist || 'Sconosciuto', title: title }});
    }}
  }});
  return songs;
}}

function exportCompareResultsToCSV() {{
  if (lastCompareMissingSongs.length === 0) return;
  const headers = ["Artista", "Titolo"];
  const rows = lastCompareMissingSongs.map(s => `"${{s.artist.replace(/"/g, '""')}}","${{s.title.replace(/"/g, '""')}}"`).join('\\n');
  const csvContent = "\ufeff" + [headers.join(','), rows].join('\\n');
  const blob = new Blob([csvContent], {{ type: 'text/csv;charset=utf-8;' }});
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  
  const myRadioKey = document.getElementById('compare-my-radio').value;
  const filename = `Brani_Mancanti_${{myRadioKey.toUpperCase()}}_${{new Date().toISOString().slice(0,10)}}.csv`;
  
  link.setAttribute("href", url);
  link.setAttribute("download", filename);
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
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
