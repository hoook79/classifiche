import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Same promo check as genera_html.py
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

# Load year cache
years_cache = {}
if os.path.exists('song_years_cache.json'):
    with open('song_years_cache.json', 'r', encoding='utf-8') as f:
        years_cache = json.load(f)

# Build a set of clean songs across RTL, RDS, Italia
combined_songs = set()
for filename in ['radio_rtl1025_history.json', 'radio_rds_history.json', 'radio_italia_history.json']:
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for item in data:
            s = clean_song_name(item['song'])
            if not is_promo(s):
                combined_songs.add(s)

need_scraping = []
for song in combined_songs:
    # check year
    year = years_cache.get(song)
    if year and year != 'N/A':
        try:
            yr_int = int(year)
            if yr_int < 2010:
                continue
        except:
            pass
    need_scraping.append(song)

# Extract primary artist names
artists = set()
for song in need_scraping:
    if ' - ' in song:
        art = song.split(' - ', 1)[0].strip()
        # split by feat, &, e, comma to get primary artist
        # e.g. "883, Max Pezzali" -> "883", "Max Pezzali"
        sep_pattern = r'\bfeat\.?\b|\bft\.?\b|\bfeaturing\b|&|\be\b|\band\b|,'
        parts = re.split(sep_pattern, art, flags=re.IGNORECASE)
        # we can search for the first part
        primary_art = parts[0].strip()
        if len(primary_art) >= 2:
            artists.add(primary_art)
    else:
        # just the song title
        pass

print(f"Total songs needing scraping: {len(need_scraping)}")
print(f"Total unique primary artists: {len(artists)}")
print("Sample artists:")
for a in sorted(artists)[:30]:
    print("  -", a)
