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

# Normalise name
def clean_song_name(s):
    s = s.strip()
    s = re.sub(r'^SRS\s+', '', s)
    s = re.sub(r'\s*\(\d{4}\)\s*$', '', s)
    return s.strip()

# Let's count unique songs in RTL, RDS, Italia
files = {
    'rtl': 'radio_rtl1025_history.json',
    'rds': 'radio_rds_history.json',
    'italia': 'radio_italia_history.json',
    'toscana': 'radio_toscana_history.json',
    'nostalgia': 'radio_nostalgia_history.json',
    'mitology': 'radio_mitology_history.json',
    'divina': 'radio_divina_history.json',
    'subasio': 'radio_subasio_history.json'
}

for name, filename in files.items():
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        songs = set()
        for item in data:
            s = clean_song_name(item['song'])
            if not is_promo(s):
                songs.add(s)
        print(f"{name}: {len(songs)} unique clean songs out of {len(data)} plays")
