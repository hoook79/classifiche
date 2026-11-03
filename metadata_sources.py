#!/usr/bin/env python3
"""
Fonti aggiuntive di metadati, utilizzabili in automatico senza accessi riservati:
- Discogs (API pubblica): autori e compositori dai crediti delle pubblicazioni
- Wikidata (dati aperti CC0): ISWC delle opere, scaricati in locale e confrontati senza ricerche per brano
- Verifica della cifra di controllo ISWC, per scartare codici errati da qualunque fonte
"""
import csv
import io
import re
import threading
import time

import requests

from db_manager import get_db_connection
from enrichment_worker import load_config, is_same_recording, _norm_title

USER_AGENT = "BroadcasterReportsApp/1.0 (contact@broadcaster-reports.it)"
WIKIDATA_REFRESH_DAYS = 30

# --- ISWC ---

def normalize_iswc(value):
    """
    Ritorna l'ISWC nel formato T-123.456.789-0 se valido (cifra di controllo compresa), altrimenti None.
    Accetta T1234567890, T-123456789-0, T-123.456.789-0 con o senza spazi.
    """
    if not value:
        return None
    m = re.fullmatch(r'T(\d{9})(\d)', re.sub(r'[\s.\-]', '', str(value).upper()))
    if not m:
        return None
    digits, check = m.group(1), int(m.group(2))
    expected = (10 - (1 + sum((i + 1) * int(d) for i, d in enumerate(digits))) % 10) % 10
    if check != expected:
        return None
    return f"T-{digits[:3]}.{digits[3:6]}.{digits[6:]}-{check}"

def _words(text):
    return {w for w in re.findall(r'\w+', (text or '').lower()) if len(w) >= 3}

# --- WIKIDATA ---

_WD_QUERY_TITLES = 'SELECT ?w ?iswc ?lab WHERE { ?w wdt:P1827 ?iswc. ?w rdfs:label ?lab. FILTER(LANG(?lab)="it" || LANG(?lab)="en") }'
# Interpreti, compositori, parolieri, autori e produttori dell'opera: servono a confermare che sia il brano giusto
_WD_QUERY_PEOPLE = 'SELECT ?w ?pl WHERE { ?w wdt:P1827 ?iswc. ?w wdt:P175|wdt:P86|wdt:P676|wdt:P50|wdt:P162 ?p. ?p rdfs:label ?pl. FILTER(LANG(?pl)="en" || LANG(?pl)="it") }'

_wd_lock = threading.Lock()
_wd_index = None  # titolo normalizzato -> [(iswc, parole delle persone collegate)]

def _wikidata_csv(query):
    r = requests.get("https://query.wikidata.org/sparql", params={"query": query},
                     headers={"Accept": "text/csv", "User-Agent": USER_AGENT}, timeout=90)
    r.raise_for_status()
    return list(csv.DictReader(io.StringIO(r.text)))

def refresh_wikidata_iswc(force=False):
    """Scarica (al massimo ogni WIKIDATA_REFRESH_DAYS giorni) l'elenco delle opere con ISWC da Wikidata nel DB locale."""
    global _wd_index
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS wikidata_iswc (titolo_norm TEXT NOT NULL, iswc TEXT NOT NULL, persone TEXT DEFAULT '')")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_wikidata_titolo ON wikidata_iswc(titolo_norm)")
    cursor.execute("CREATE TABLE IF NOT EXISTS fonti_aggiornamento (fonte TEXT PRIMARY KEY, data TEXT)")
    row = cursor.execute("SELECT data FROM fonti_aggiornamento WHERE fonte = 'wikidata_iswc' AND data >= date('now', ?)",
                         (f"-{WIKIDATA_REFRESH_DAYS} day",)).fetchone()
    if row and not force:
        conn.close()
        return 0

    try:
        titles = _wikidata_csv(_WD_QUERY_TITLES)
        people = _wikidata_csv(_WD_QUERY_PEOPLE)
    except Exception as e:
        print(f"[WIKIDATA] Download non riuscito, uso i dati già presenti: {e}")
        conn.close()
        return 0

    people_by_work = {}
    for p in people:
        people_by_work.setdefault(p["w"], set()).add(p["pl"])
    records = set()
    for t in titles:
        iswc = normalize_iswc(t["iswc"])
        title_norm = _norm_title(t["lab"])
        if iswc and title_norm:
            records.add((title_norm, iswc, "|".join(sorted(people_by_work.get(t["w"], [])))))

    cursor.execute("DELETE FROM wikidata_iswc")
    cursor.executemany("INSERT INTO wikidata_iswc (titolo_norm, iswc, persone) VALUES (?, ?, ?)", records)
    cursor.execute("INSERT OR REPLACE INTO fonti_aggiornamento (fonte, data) VALUES ('wikidata_iswc', date('now'))")
    conn.commit()
    conn.close()
    with _wd_lock:
        _wd_index = None
    print(f"[WIKIDATA] Elenco ISWC aggiornato: {len(records)} opere.")
    return len(records)

def _load_wikidata_index():
    global _wd_index
    with _wd_lock:
        if _wd_index is None:
            index = {}
            conn = get_db_connection()
            try:
                for r in conn.execute("SELECT titolo_norm, iswc, persone FROM wikidata_iswc"):
                    index.setdefault(r["titolo_norm"], []).append((r["iswc"], _words(r["persone"])))
            except Exception:
                pass  # tabella non ancora creata: nessun dato Wikidata
            conn.close()
            _wd_index = index
        return _wd_index

def find_iswc_wikidata(artist, title, composers="", authors=""):
    """
    ISWC da Wikidata per titolo identico, confermato da almeno un nome in comune tra
    interprete/autori del brano e persone collegate all'opera. Se le opere possibili hanno ISWC diversi, nessun risultato.
    """
    candidates = _load_wikidata_index().get(_norm_title(title), [])
    if not candidates:
        return None
    names = _words(artist) | _words(composers) | _words(authors)
    matches = {iswc for iswc, people in candidates if names & people}
    return matches.pop() if len(matches) == 1 else None

# --- DISCOGS ---

_discogs_lock = threading.Lock()
_discogs_last_call = 0.0
_WRITER_ROLES = re.compile(r'written|songwriter', re.I)
_COMPOSER_ROLES = re.compile(r'music by|composed', re.I)
_LYRICIST_ROLES = re.compile(r'lyrics|words by', re.I)

def _discogs_get(url, params=None):
    """GET su Discogs nel limite di richieste: 25/min senza chiave, 60/min con 'discogs_token' in config.json."""
    global _discogs_last_call
    token = load_config().get("discogs_token")
    interval = 1.1 if token else 2.6
    with _discogs_lock:
        wait = interval - (time.time() - _discogs_last_call)
        if wait > 0:
            time.sleep(wait)
        _discogs_last_call = time.time()
    headers = {"User-Agent": USER_AGENT}
    if token:
        headers["Authorization"] = f"Discogs token={token}"
    r = requests.get(url, params=params, headers=headers, timeout=15)
    return r.json() if r.status_code == 200 else {}

def search_discogs_writers(artist, title):
    """Cerca i crediti di scrittura del brano su Discogs. Ritorna (compositori, autori) come stringhe, o (None, None)."""
    main_artist = re.split(r',| & | feat\.? | ft\.? | x ', artist or '', flags=re.I)[0].strip()
    try:
        res = _discogs_get("https://api.discogs.com/database/search",
                           {"artist": main_artist, "track": _norm_title(title) or title, "type": "release", "per_page": 5})
        for release in res.get("results", [])[:2]:
            data = _discogs_get(f"https://api.discogs.com/releases/{release['id']}")
            if not data:
                continue
            credits = []
            for track in data.get("tracklist", []):
                if not is_same_recording(artist, title, artist, track.get("title")):
                    continue
                credits += track.get("extraartists", [])
                position = track.get("position") or ""
                # Crediti a livello di pubblicazione che valgono per tutte le tracce o per questa
                credits += [c for c in data.get("extraartists", []) if not c.get("tracks") or position in c.get("tracks", "")]
            composers, lyricists = [], []
            for c in credits:
                name = re.sub(r'\s*\(\d+\)$', '', c.get("name", "")).strip()
                role = c.get("role", "")
                if not name:
                    continue
                if (_WRITER_ROLES.search(role) or _COMPOSER_ROLES.search(role)) and name not in composers:
                    composers.append(name)
                if (_WRITER_ROLES.search(role) or _LYRICIST_ROLES.search(role)) and name not in lyricists:
                    lyricists.append(name)
            if composers or lyricists:
                return (", ".join(composers) or None), (", ".join(lyricists) or None)
    except Exception as e:
        print(f"[DISCOGS] Errore per '{artist} - {title}': {e}")
    return None, None

def apply_wikidata_iswc():
    """Assegna l'ISWC da Wikidata a tutti i brani che non l'hanno (una volta per gruppo di varianti). Ritorna quanti."""
    from db_manager import update_metadata
    conn = get_db_connection()
    empty = "('', '-', 'N/A', 'N/D')"
    rows = conn.execute(f"""
        SELECT * FROM canzoni_metadati
        WHERE codice_iswc IS NULL OR TRIM(codice_iswc) IN {empty}
        GROUP BY chiave
    """).fetchall()
    conn.close()
    assigned = 0
    for r in rows:
        iswc = find_iswc_wikidata(r["artista_pulito"], r["titolo_pulito"], r["compositore"], r["autore"])
        if not iswc:
            continue
        update_metadata(r["artista_pulito"], r["titolo_pulito"], r["codice_siae"] or "", iswc, r["codice_isrc"] or "",
                        r["compositore"] or "", r["autore"] or "", r["casa_discografica"] or "", r["anno_pubblicazione"] or "")
        assigned += 1
    return assigned
