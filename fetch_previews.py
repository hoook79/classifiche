#!/usr/bin/env python3
"""
fetch_previews.py
Cerca anteprime audio 30s (iTunes + Deezer) per le canzoni monitorate.
Salva in preview_cache.json — genera_html.py incorpora gli URL nell'HTML.

Eseguire da Windows dove c'è accesso a internet.
"""

import json, os, re, time, unicodedata, sys

# Fix UnicodeEncodeError on Windows (cp1252 non supporta caratteri come ✓ →)
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except AttributeError:
        pass

import requests
from collections import defaultdict

BASE           = os.path.dirname(os.path.abspath(__file__))
PREVIEW_CACHE  = os.path.join(BASE, 'preview_cache.json')
SUBASIO_JSON   = os.path.join(BASE, 'radio_subasio_history.json')
DIVINA_JSON    = os.path.join(BASE, 'radio_divina_history.json')
MITOLOGY_JSON  = os.path.join(BASE, 'radio_mitology_history.json')
NOSTALGIA_JSON = os.path.join(BASE, 'radio_nostalgia_history.json')
TOSCANA_JSON   = os.path.join(BASE, 'radio_toscana_history.json')

TOP_N_PER_RADIO = 999999  # nessun limite: tutte le canzoni
DELAY_S         = 0.3   # secondi tra chiamate API

# Circuit breaker iTunes: se fallisce troppe volte di fila, salta temporaneamente
_itunes_failures = 0
_itunes_skip_until = 0  # timestamp fino a cui saltare iTunes

# ── Normalizzazione per matching ──────────────────────────────────────────────
def norm(s):
    s = (s or '').lower()
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = re.sub(r'[^a-z0-9 ]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()

def score_pair(r_artist, r_title, q_artist, q_title):
    ra, rt = norm(r_artist), norm(r_title)
    al, tl = norm(q_artist), norm(q_title)
    sa = 8 if ra==al else (5 if (al in ra or ra in al) else
         sum(2 for w in al.split() if len(w)>2 and w in ra))
    st = 8 if rt==tl else (5 if (tl in rt or rt in tl) else
         sum(2 for w in tl.split() if len(w)>2 and w in rt))
    return sa, st

# ── Parsing canzoni (stesso di genera_html.py) ────────────────────────────────
_PROMO_PHONE = re.compile(
    r'\d{9,}|\b\d{3}[\s\-./]\d{2}[\s\-./]\d{2}[\s\-./]\d{2,}|\b\d{3}[\s\-./]\d{6,}',
    re.IGNORECASE)
_PROMO_KW = re.compile(
    r'\bvocale\b|\bwhatsapp\b|\binvia\s+sms\b|\bmanda\s+(un|ora)\s'
    r'|\bchiama\s+(il|ora|e)\s|\bsintonizzat|\bascoltaci\b'
    r'|\bseguici\b|\biscriviti\b|\babbonati\b|\bgiornale\s+radio\b'
    r'|\btg\s+radio\b|\b(meteo|traffico|oroscopo)\b|\bnotiziario\b'
    r'|\bspot\s+pub|\bjingle\b(?!\s+bells)|\bgingle\b|\bstacco\b'
    r'|\bwebradio\b|\bpromo\b|\bident\b|\bsponsor\b'
    r'|\bora\s+esatta\b|\bpubblicit[aà]\b', re.IGNORECASE)
_RADIO_ALONE = re.compile(
    r'^(radio\s+)?(subasio|divina|nostalgia|mitology|toscana|deejay|italia|'
    r'rtl\b|rai\b|105\b|m2o|virgin|r101|capital|freccia|gold|kiss\s*kiss|'
    r'monte\s*carlo|studio\s*54|network|antenna)\b', re.IGNORECASE)

def is_promo(s):
    s = s.strip()
    if len(s) < 4: return True
    if _PROMO_PHONE.search(s): return True
    if _PROMO_KW.search(s): return True
    if ' - ' not in s and _RADIO_ALONE.match(s): return True
    return False

def collect_songs_from_json(filepath, parse_fn, top_n=None):
    """Legge un JSON e ritorna dict {(artist,title): count}. top_n=None → tutte."""
    counts = defaultdict(int)
    if not os.path.exists(filepath):
        return counts
    with open(filepath, 'r', encoding='utf-8') as f:
        history = json.load(f)
    for item in history:
        raw = item.get('song', '').strip()
        if is_promo(raw):
            continue
        artist, title = parse_fn(raw)
        if artist and title:
            counts[(artist, title)] += 1
    sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    if top_n:
        sorted_items = sorted_items[:top_n]
    return dict(sorted_items)

def parse_generic(raw):
    year_m = re.search(r'\((\d{4})\)\s*$', raw)
    cleaned = re.sub(r'\s*\(\d{4}\)\s*$', '', raw).strip()
    if ' - ' in cleaned:
        a, t = cleaned.split(' - ', 1)
        return a.strip().title(), t.strip().title()
    return cleaned.title(), ''

def parse_subasio(raw):
    raw = re.sub(r'^SRS\s+', '', raw).strip()
    if ' - ' in raw:
        a, t = raw.split(' - ', 1)
        return a.strip(), t.strip()
    return raw.strip(), ''

# ── Ricerca anteprima (iTunes + Deezer) ───────────────────────────────────────
def find_preview(artist, title, session):
    """Cerca su iTunes poi Deezer. Ritorna (url, sorgente) o (None, None)."""
    global _itunes_failures, _itunes_skip_until

    # --- iTunes (con circuit breaker) ---
    now = time.time()
    if now >= _itunes_skip_until:
        try:
            q = f"{artist} {title}"
            resp = session.get(
                f"https://itunes.apple.com/search"
                f"?term={requests.utils.quote(q)}&entity=song&limit=15&media=music",
                timeout=8
            )
            if resp.status_code == 200 and resp.text.strip():
                results = [r for r in resp.json().get('results', []) if r.get('previewUrl')]
                results.sort(key=lambda r: sum(score_pair(
                    r.get('artistName',''), r.get('trackName',''), artist, title
                )), reverse=True)
                if results:
                    sa, st = score_pair(
                        results[0].get('artistName',''), results[0].get('trackName',''),
                        artist, title)
                    if sa >= 3 and st >= 3:
                        _itunes_failures = 0  # reset failures on success
                        return results[0]['previewUrl'], 'iTunes'
                _itunes_failures = 0  # risposta valida anche senza risultati
            else:
                # Risposta vuota o errore HTTP → rate limit
                _itunes_failures += 1
                if _itunes_failures >= 3:
                    wait_min = min(5 * _itunes_failures, 30)  # 15s, 20s, ... max 30s
                    _itunes_skip_until = time.time() + wait_min
                    print(f"    [iTunes] rate-limit rilevato ({_itunes_failures}x), pausa {wait_min}s")
        except Exception as e:
            _itunes_failures += 1
            if _itunes_failures >= 3:
                wait_min = min(5 * _itunes_failures, 30)
                _itunes_skip_until = time.time() + wait_min
                print(f"    [iTunes] errore ({e}), pausa {wait_min}s")
            else:
                print(f"    iTunes error: {e}")
        time.sleep(DELAY_S)
    else:
        secs_left = int(_itunes_skip_until - now)
        if secs_left % 30 == 0 and secs_left > 0:  # stampa solo ogni 30s per non spammare
            print(f"    [iTunes] in pausa per altri {secs_left}s")

    # --- Deezer: prima ricerca avanzata, poi semplice ---
    queries = [f'artist:"{artist}" track:"{title}"', f"{artist} {title}"]
    for q in queries:
        try:
            resp = session.get(
                f"https://api.deezer.com/search"
                f"?q={requests.utils.quote(q)}&limit=15",
                timeout=8
            )
            results = [r for r in resp.json().get('data', []) if r.get('preview')]
            results.sort(key=lambda r: sum(score_pair(
                r.get('artist',{}).get('name',''), r.get('title',''),
                artist, title
            )), reverse=True)
            if results:
                sa, st = score_pair(
                    results[0].get('artist',{}).get('name',''),
                    results[0].get('title',''), artist, title)
                if sa >= 3 and st >= 3:
                    return results[0]['preview'], 'Deezer'
        except Exception as e:
            print(f"    Deezer error ({q[:30]}): {e}")
        time.sleep(DELAY_S)

    return None, None

# ── Main ──────────────────────────────────────────────────────────────────────
print("=" * 60)
print("fetch_previews.py — Ricerca anteprime audio")
print("=" * 60)

def is_url_expired(url):
    """Controlla se un URL Deezer CDN ha un token exp= scaduto."""
    if not url or 'dzcdn.net' not in url:
        return False  # iTunes e None non scadono
    m = re.search(r'exp=(\d+)', url)
    if not m:
        return False
    return int(m.group(1)) < time.time()

# Carica cache esistente
cache = {}
if os.path.exists(PREVIEW_CACHE):
    with open(PREVIEW_CACHE, 'r', encoding='utf-8') as f:
        cache = json.load(f)
    expired = sum(1 for v in cache.values() if is_url_expired(v))
    print(f"Cache esistente: {len(cache)} brani ({sum(1 for v in cache.values() if v)} con URL, {expired} Deezer scaduti)")

# Raccogli canzoni da tutte le radio
print("\nRaccolta canzoni...")
all_songs = defaultdict(int)

radios = [
    (SUBASIO_JSON,   parse_subasio,  'Subasio'),
    (DIVINA_JSON,    parse_generic,  'Divina'),
    (MITOLOGY_JSON,  parse_generic,  'Mitology'),
    (NOSTALGIA_JSON, parse_generic,  'Nostalgia'),
    (TOSCANA_JSON,   parse_generic,  'Toscana'),
]
for filepath, parse_fn, label in radios:
    songs = collect_songs_from_json(filepath, parse_fn)  # tutti i brani
    for (artist, title), count in songs.items():
        all_songs[(artist, title)] += count
    print(f"  {label}: {len(songs)} brani")

# Ordina per popolarità totale
sorted_songs = sorted(all_songs.items(), key=lambda x: x[1], reverse=True)
print(f"\nTotale brani unici da cercare: {len(sorted_songs)}")

# Filtra: solo brani NON ancora in cache.
# Le URL Deezer scadute NON vengono ri-scaricate qui: il JS le cerca live.
# Solo gli URL iTunes (permanenti) e None vengono mantenuti.
def needs_fetch(artist, title):
    key = (artist + '|' + title).lower()
    return key not in cache  # True solo per brani nuovi

to_fetch = [
    (artist, title, count)
    for (artist, title), count in sorted_songs
    if needs_fetch(artist, title)
]
deezer_cached = sum(1 for v in cache.values() if v and 'dzcdn.net' in v)
print(f"Da cercare: {len(to_fetch)} nuovi brani (Deezer in cache: {deezer_cached} - gestiti live via JS)")

if not to_fetch:
    print("\nNessun brano da aggiornare. Cache già completa.")
else:
    session = requests.Session()
    session.headers.update({'User-Agent': 'RadioCharts/1.0 (preview-fetcher)'})

    found = 0
    not_found = 0
    for i, (artist, title, plays) in enumerate(to_fetch, 1):
        key = (artist + '|' + title).lower()
        print(f"  [{i}/{len(to_fetch)}] {artist} – {title} ({plays} pass.)", end='  ')
        url, source = find_preview(artist, title, session)
        if url:
            print(f"OK {source}")
            found += 1
        else:
            print("-- non trovata")
            not_found += 1
        cache[key] = url  # None se non trovata

        # Salva ogni 20 brani per non perdere progressi
        if i % 20 == 0:
            with open(PREVIEW_CACHE, 'w', encoding='utf-8') as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
            print(f"  -> Cache salvata ({i} processati)")

    # Salvataggio finale
    with open(PREVIEW_CACHE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

    print(f"\nRisultati: {found} con anteprima, {not_found} senza.")

print(f"\nCache totale: {len(cache)} brani")
print(f"Con URL:      {sum(1 for v in cache.values() if v)}")
print(f"Senza URL:    {sum(1 for v in cache.values() if v is None)}")
print("\nEsegui ora genera_html.py per incorporare gli URL nell'HTML.")
