#!/usr/bin/env python3
import http.server
import socketserver
import json
import os
import subprocess
import sys
import urllib.parse
import io
import csv
import xlsxwriter
import re
import time
import threading
import concurrent.futures

def sanitize_for_siae(text):
    if not text:
        return ""
    replacements = {
        'à': "a'", 'á': "a'", 'ä': "a",
        'è': "e'", 'é': "e'", 'ë': "e",
        'ì': "i'", 'í': "i'", 'ï': "i",
        'ò': "o'", 'ó': "o'", 'ö': "o",
        'ù': "u'", 'ú': "u'", 'ü': "u",
        'À': "A'", 'È': "E'", 'Ì': "I'", 'Ò': "O'", 'Ù': "U'"
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    text = re.sub(r'[~©®™]', '', text)
    return text


# Aggiungi cartella corrente al path per caricare i moduli locali
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
sys.path.append(DIRECTORY)

from db_manager import get_db_connection, update_metadata, get_monthly_unique_songs, insert_passage, month_range, get_available_months, init_db, ensure_song_keys, song_key
from log_parser import parse_log_file
from scraper_retro import scrape_retro
from data_cleaner import clean_song

LOG_FILE = os.path.join(DIRECTORY, 'server_output.log')

if sys.stdout is not None:
    try:
        sys.stdout.write("========================================================\n")
        sys.stdout.write("  [SERVER] AVVIO SERVER CLASSIFICHE RADIO IN CORSO...\n")
        sys.stdout.write("  I log saranno salvati in: server_output.log\n")
        sys.stdout.write("========================================================\n\n")
        sys.stdout.flush()
    except Exception:
        pass

try:
    log_f = open(LOG_FILE, 'a', encoding='utf-8', buffering=1)
    sys.stdout = log_f
    sys.stderr = log_f
except Exception:
    devnull = open(os.devnull, 'w')
    sys.stdout = devnull
    sys.stderr = devnull

PORT = 8000

def find_year(artist, title):
    song_query = f"{artist} - {title}"
    try:
        from fetch_years import (
            get_year_from_musicbrainz,
            get_year_from_itunes,
            get_year_from_genius,
            get_year_from_wikipedia,
            is_valid_year_for_song
        )
        
        # 1. Prova MusicBrainz
        candidate = get_year_from_musicbrainz(song_query)
        if candidate != "N/A" and is_valid_year_for_song(song_query, candidate):
            print(f"  [SEARCH YEAR] MusicBrainz validato: {candidate}")
            return candidate
            
        # 2. Prova iTunes
        candidate = get_year_from_itunes(song_query)
        if candidate != "N/A" and is_valid_year_for_song(song_query, candidate):
            print(f"  [SEARCH YEAR] iTunes validato: {candidate}")
            return candidate
            
        # 3. Prova Genius
        candidate = get_year_from_genius(song_query)
        if candidate != "N/A" and is_valid_year_for_song(song_query, candidate):
            print(f"  [SEARCH YEAR] Genius validato: {candidate}")
            return candidate
            
        # 4. Prova Wikipedia
        candidate = get_year_from_wikipedia(song_query)
        if candidate != "N/A" and is_valid_year_for_song(song_query, candidate):
            print(f"  [SEARCH YEAR] Wikipedia validato: {candidate}")
            return candidate
            
    except Exception as e:
        print(f"Errore durante ricerca anno: {e}")
    return "N/A"

def find_radio_date(artist, title):
    song_db = f"{artist} - {title}"
    try:
        from scrape_earone_radiodates import search_earone, match_score, format_date, search_earone_via_web
        
        # 1. Prova ricerca mirata f"{artist} {title}"
        song_results = search_earone(f"{artist} {title}")
        best_score = 0
        best_item = None
        for res in song_results:
            res_song = res.get('song', {})
            res_artists = ", ".join([a.get('name') for a in res_song.get('tracks', [{}])[0].get('artists', [])]) if res_song.get('tracks') else "Unknown"
            res_title = res_song.get('title', '')
            score = match_score(artist, title, res_artists, res_title)
            if score > best_score:
                best_score = score
                best_item = res
                
        if best_item and best_score >= 80:
            formatted = format_date(best_item.get('radioDate'))
            print(f"  [SEARCH RD] Trovata da query diretta EarOne: {formatted} (Score: {best_score})")
            return formatted
            
        # 2. Prova ricerca per solo titolo
        title_results = search_earone(title)
        best_score = 0
        best_item = None
        for res in title_results:
            res_song = res.get('song', {})
            res_artists = ", ".join([a.get('name') for a in res_song.get('tracks', [{}])[0].get('artists', [])]) if res_song.get('tracks') else "Unknown"
            res_title = res_song.get('title', '')
            score = match_score(artist, title, res_artists, res_title)
            if score > best_score:
                best_score = score
                best_item = res
                
        if best_item and best_score >= 80:
            formatted = format_date(best_item.get('radioDate'))
            print(f"  [SEARCH RD] Trovata da query titolo EarOne: {formatted} (Score: {best_score})")
            return formatted
            
        # 3. Web search fallback
        web_date = search_earone_via_web(song_db)
        if web_date != "N/A":
            print(f"  [SEARCH RD] Trovata da Web Fallback: {web_date}")
            return web_date
            
    except Exception as e:
        print(f"Errore durante ricerca radio date: {e}")
    return "N/A"

RADIOS = [
    {"id": "subasio", "name": "Radio Subasio"},
    {"id": "divina", "name": "Radio Divina"},
    {"id": "mitology", "name": "Radio Mitology"},
    {"id": "nostalgia", "name": "Radio Nostalgia"},
    {"id": "toscana", "name": "Radio Toscana"},
    {"id": "italia", "name": "Radio Italia"},
    {"id": "rds", "name": "RDS"},
    {"id": "rtl1025", "name": "RTL 102.5"},
    {"id": "birikina", "name": "Radio Birikina"},
    {"id": "bruno", "name": "Radio Bruno"},
    {"id": "kisskiss", "name": "Radio Kiss Kiss"},
    {"id": "m2o", "name": "Radio m2o"},
    {"id": "propostaaosta", "name": "Proposta Aosta"},
    {"id": "capital", "name": "Radio Capital"}
]
RADIO_NAMES = {r["id"]: r["name"] for r in RADIOS}

METADATA_FIELDS = ["codice_siae", "codice_iswc", "codice_isrc", "compositore", "autore", "casa_discografica", "anno_pubblicazione"]

def is_empty(val):
    return not val or str(val).strip() in ['', '-', 'N/A', 'N/D']

def apply_song_status(song):
    """Calcola semaforo e campi mancanti di un brano (modifica il dict e lo ritorna)."""
    has_siae = not is_empty(song["codice_siae"])
    has_iswc = not is_empty(song["codice_iswc"])
    has_isrc = not is_empty(song["codice_isrc"])
    has_writer = not (is_empty(song["compositore"]) and is_empty(song["autore"]))
    has_label_or_year = not (is_empty(song["casa_discografica"]) and is_empty(song["anno_pubblicazione"]))

    missing = []
    if not (has_siae or has_iswc):
        missing.append("SIAE/ISWC")
    if not has_isrc:
        missing.append("ISRC")
    if not has_writer:
        missing.append("Autori")
    if not has_label_or_year:
        missing.append("Label/Anno")

    if not missing:
        song["status"] = "green"
    elif len(missing) == 4:
        song["status"] = "red"
    else:
        song["status"] = "yellow"
    song["mancanti"] = missing
    return song

# Cache in memoria dei brani per (mese, radio): la query mensile si esegue una volta sola,
# poi filtri, ricerca e paginazione lavorano in memoria. Scade dopo CACHE_TTL secondi
# perché i poller inseriscono nuovi passaggi da processi separati.
CACHE_TTL = 300
_songs_cache = {}
_songs_cache_lock = threading.Lock()

def get_songs_cached(month, radio_id, refresh=False):
    key = (month, radio_id or "all")
    now = time.time()
    with _songs_cache_lock:
        entry = _songs_cache.get(key)
        if entry and not refresh and now - entry[0] < CACHE_TTL:
            return entry[1]

    ensure_song_keys()  # chiave per le righe aggiunte nel frattempo dagli altri script

    # Le varianti dello stesso brano (maiuscole/accenti diversi) diventano una riga sola:
    # passaggi sommati, nome mostrato = variante più trasmessa
    groups = {}
    for row in get_monthly_unique_songs(month, radio_id):
        key = row["chiave"] or song_key(row["artista_pulito"], row["titolo_pulito"])
        groups.setdefault(key, []).append(row)

    songs = []
    for key, rows in groups.items():
        main = max(rows, key=lambda r: r["passaggi"])
        richest = max(rows, key=lambda r: sum(not is_empty(r[f]) for f in METADATA_FIELDS))
        song = {
            "chiave": key,
            "artista_pulito": main["artista_pulito"],
            "titolo_pulito": main["titolo_pulito"],
            "passaggi": sum(r["passaggi"] for r in rows),
            "varianti": len(rows)
        }
        for field in METADATA_FIELDS:
            song[field] = richest[field] or ""
        songs.append(apply_song_status(song))

    with _songs_cache_lock:
        if len(_songs_cache) > 30:
            _songs_cache.clear()
        _songs_cache[key] = (now, songs)
    return songs

def invalidate_songs_cache():
    with _songs_cache_lock:
        _songs_cache.clear()

def update_cached_song(artist_clean, title_clean, values):
    """Aggiorna il brano (tutte le sue varianti) in tutte le liste in cache, senza rieseguire le query."""
    key = song_key(artist_clean, title_clean)
    with _songs_cache_lock:
        for _, songs in _songs_cache.values():
            for song in songs:
                if song["chiave"] == key:
                    song.update(values)
                    apply_song_status(song)

STATUS_ORDER = {"red": 0, "yellow": 1, "green": 2}

def filter_songs(songs, q, status, sort):
    result = songs
    if status in ("green", "yellow", "red"):
        result = [s for s in result if s["status"] == status]
    elif status == "incomplete":
        result = [s for s in result if s["status"] != "green"]
    if q:
        terms = q.lower().split()
        def matches(s):
            text = " ".join([s["artista_pulito"], s["titolo_pulito"], s["codice_siae"], s["codice_iswc"], s["codice_isrc"], s["compositore"], s["autore"]]).lower()
            return all(t in text for t in terms)
        result = [s for s in result if matches(s)]

    if sort == "artist":
        result = sorted(result, key=lambda s: (s["artista_pulito"].lower(), s["titolo_pulito"].lower()))
    elif sort == "title":
        result = sorted(result, key=lambda s: (s["titolo_pulito"].lower(), s["artista_pulito"].lower()))
    elif sort == "status":
        result = sorted(result, key=lambda s: (STATUS_ORDER[s["status"]], -s["passaggi"]))
    else:
        result = sorted(result, key=lambda s: (-s["passaggi"], s["artista_pulito"].lower()))
    return result

# Invio a Google Sheets solo dei brani modificati, raggruppati ogni pochi secondi.
# La sincronizzazione completa dopo ogni salvataggio era lenta e poteva riportare
# sul DB il vecchio valore presente nel foglio.
_sheets_queue = set()
_sheets_lock = threading.Lock()
_sheets_timer = None

def queue_sheets_push(artist_clean, title_clean):
    global _sheets_timer
    with _sheets_lock:
        _sheets_queue.add((artist_clean, title_clean))
        if _sheets_timer is None:
            _sheets_timer = threading.Timer(5.0, _flush_sheets_queue)
            _sheets_timer.daemon = True
            _sheets_timer.start()

def _flush_sheets_queue():
    global _sheets_timer
    with _sheets_lock:
        keys = list(_sheets_queue)
        _sheets_queue.clear()
        _sheets_timer = None
    try:
        from google_sheets_sync import push_metadata_rows
        push_metadata_rows(keys)
    except Exception as e:
        print(f"Errore invio righe a Google Sheets: {e}")

_spotify_token = {"value": None, "expires": 0.0}

def lookup_song_online(artist, title, isrc=None):
    """
    Cerca i metadati di un singolo brano interrogando in parallelo Spotify, Deezer, iTunes e MusicBrainz.
    Non salva nulla: ritorna i valori trovati con la fonte, da confermare nel pannello.
    """
    from enrichment_worker import load_config, get_spotify_token, search_spotify, search_deezer, search_itunes
    from bulk_enrichment import rate_limited_search_musicbrainz
    from metadata_sources import search_discogs_writers, find_iswc_wikidata, normalize_iswc

    if time.time() > _spotify_token["expires"]:
        config = load_config()
        token = get_spotify_token(config.get("spotify_client_id"), config.get("spotify_client_secret"))
        _spotify_token["value"] = token
        _spotify_token["expires"] = time.time() + (3000 if token else 600)
    token = _spotify_token["value"]

    def safe(fn, *args, size=3):
        try:
            res = fn(*args)
            return res if res else (None,) * size
        except Exception as e:
            print(f"[LOOKUP] Errore {fn.__name__} per '{artist} - {title}': {e}")
            return (None,) * size

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
        f_spotify = ex.submit(safe, search_spotify, artist, title, token) if token else None
        f_deezer = ex.submit(safe, search_deezer, artist, title)
        f_itunes = ex.submit(safe, search_itunes, artist, title, size=2)
        f_mb = ex.submit(safe, rate_limited_search_musicbrainz, artist, title, isrc)
        f_dc = ex.submit(safe, search_discogs_writers, artist, title, size=2)
        sp = f_spotify.result() if f_spotify else (None, None, None)
        dz = f_deezer.result()
        it = f_itunes.result()
        mb = f_mb.result()
        dc = f_dc.result()

    found = {}
    def pick(field, candidates):
        for value, source in candidates:
            if not is_empty(value):
                found[field] = {"value": str(value).strip(), "source": source}
                return

    pick("codice_isrc", [(sp[0], "Spotify"), (dz[0], "Deezer")])
    pick("anno_pubblicazione", [(sp[1], "Spotify"), (dz[1], "Deezer"), (it[0], "iTunes")])
    pick("casa_discografica", [(sp[2], "Spotify"), (dz[2], "Deezer"), (it[1], "iTunes")])
    pick("compositore", [(mb[1], "MusicBrainz"), (dc[0], "Discogs")])
    pick("autore", [(mb[2], "MusicBrainz"), (dc[1], "Discogs")])
    composers = found.get("compositore", {}).get("value", "")
    authors = found.get("autore", {}).get("value", "")
    pick("codice_iswc", [(normalize_iswc(mb[0]), "MusicBrainz"),
                         (find_iswc_wikidata(artist, title, composers, authors), "Wikidata")])
    return found

def get_bordereau_rows(month, radio_id, mode):
    ensure_song_keys()
    conn = get_db_connection()
    params = list(month_range(month))
    radio_filter = ""
    if radio_id:
        radio_filter = " AND p.id_radio = ?"
        params.append(radio_id)
    if mode == "detail":
        sql = f"""
        SELECT p.data, p.ora, p.durata, p.titolo, p.artista,
               m.codice_siae, m.codice_iswc, m.autore, m.compositore
        FROM passaggi p
        LEFT JOIN canzoni_metadati m ON p.artista_pulito = m.artista_pulito AND p.titolo_pulito = m.titolo_pulito
        WHERE p.data >= ? AND p.data < ?{radio_filter}
        ORDER BY p.data ASC, p.ora ASC
        """
    else:
        sql = f"""
        SELECT p.titolo_pulito AS titolo, p.artista_pulito AS artista,
               COUNT(*) AS passaggi, SUM(p.durata) AS durata,
               m.codice_siae, m.codice_iswc, m.autore, m.compositore
        FROM passaggi p
        LEFT JOIN canzoni_metadati m ON p.artista_pulito = m.artista_pulito AND p.titolo_pulito = m.titolo_pulito
        WHERE p.data >= ? AND p.data < ?{radio_filter}
        GROUP BY COALESCE(m.chiave, p.artista_pulito || '|' || p.titolo_pulito)
        ORDER BY p.titolo_pulito, p.artista_pulito
        """
    rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
    conn.close()
    for r in rows:
        for k in ("codice_siae", "codice_iswc", "autore", "compositore"):
            r[k] = "" if is_empty(r.get(k)) else r[k]
    return rows

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def send_json(self, payload, code=200):
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json_body(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length <= 0:
            return {}
        return json.loads(self.rfile.read(content_length).decode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        # 1. API: List emittenti
        if path == '/api/enrichment/status':
            try:
                progress_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scratch', 'enrichment_progress.json')
                status_data = {"status": "idle", "total": 0, "processed": 0, "success": 0, "elapsed": 0.0}
                if os.path.exists(progress_file):
                    with open(progress_file, 'r', encoding='utf-8') as f:
                        status_data = json.load(f)
                
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(status_data).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
            return
            
        elif path == '/api/radios':
            radios_list = RADIOS
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(radios_list).encode('utf-8'))
            return

        elif path == '/api/months':
            try:
                self.send_json({"success": True, "months": get_available_months()})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, 500)
            return

        # 2. API: Dati Dashboard (filtri, ricerca e paginazione lato server)
        elif path == '/api/dashboard_data':
            month = query.get('month', [''])[0] # YYYY-MM
            radio_id = query.get('radio_id', [None])[0]
            if radio_id == 'all' or not radio_id:
                radio_id = None

            if not month:
                self.send_json({"success": False, "error": "Parametro month richiesto (YYYY-MM)"}, 400)
                return

            try:
                q = query.get('q', [''])[0].strip()
                status = query.get('status', ['all'])[0]
                sort = query.get('sort', ['plays'])[0]
                page = max(1, int(query.get('page', ['1'])[0] or 1))
                size = min(500, max(10, int(query.get('size', ['100'])[0] or 100)))
                refresh = query.get('refresh', ['0'])[0] == '1'

                songs = get_songs_cached(month, radio_id, refresh)
                stats = {"total": len(songs), "green": 0, "yellow": 0, "red": 0, "plays": 0, "plays_green": 0}
                for song in songs:
                    stats[song["status"]] += 1
                    stats["plays"] += song["passaggi"]
                    if song["status"] == "green":
                        stats["plays_green"] += song["passaggi"]

                filtered = filter_songs(songs, q, status, sort)
                pages = max(1, (len(filtered) + size - 1) // size)
                page = min(page, pages)

                self.send_json({
                    "success": True,
                    "songs": filtered[(page - 1) * size: page * size],
                    "stats": stats,
                    "filtered": len(filtered),
                    "page": page,
                    "pages": pages,
                    "size": size
                })
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, 500)
            return

        # API: Dati per l'anteprima di stampa del borderò
        elif path == '/api/bordereau':
            month = query.get('month', [''])[0]
            radio_id = query.get('radio_id', [None])[0]
            if radio_id == 'all' or not radio_id:
                radio_id = None
            mode = query.get('mode', ['summary'])[0]
            if not month:
                self.send_json({"success": False, "error": "Parametro month richiesto (YYYY-MM)"}, 400)
                return
            if mode == 'detail' and not radio_id:
                self.send_json({"success": False, "error": "Il dettaglio passaggi richiede una singola radio"}, 400)
                return
            try:
                self.send_json({
                    "success": True,
                    "month": month,
                    "radio_id": radio_id or "all",
                    "radio_name": RADIO_NAMES.get(radio_id, radio_id) if radio_id else "Tutte le emittenti",
                    "mode": mode,
                    "rows": get_bordereau_rows(month, radio_id, mode)
                })
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, 500)
            return

        # 3. Report SCF (Excel)
        elif path == '/api/export/scf':
            month = query.get('month', [''])[0]
            radio_id = query.get('radio_id', [None])[0]
            if radio_id == 'all' or not radio_id:
                radio_id = None
                
            if not month:
                self.send_response(400)
                self.end_headers()
                return

            try:
                ensure_song_keys()
                conn = get_db_connection()
                cursor = conn.cursor()
                sql = '''
                SELECT
                    p.artista_pulito,
                    p.titolo_pulito, 
                    COUNT(*) as passaggi, 
                    SUM(p.durata) as secondi,
                    m.casa_discografica,
                    m.anno_pubblicazione,
                    m.codice_isrc
                FROM passaggi p
                LEFT JOIN canzoni_metadati m ON p.artista_pulito = m.artista_pulito AND p.titolo_pulito = m.titolo_pulito
                WHERE p.data >= ? AND p.data < ?
                '''
                params = list(month_range(month))
                if radio_id:
                    sql += " AND p.id_radio = ?"
                    params.append(radio_id)
                sql += " GROUP BY COALESCE(m.chiave, p.artista_pulito || '|' || p.titolo_pulito) ORDER BY passaggi DESC"
                
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                conn.close()
                
                output = io.BytesIO()
                workbook = xlsxwriter.Workbook(output)
                worksheet = workbook.add_worksheet('Report SCF')
                
                headers = ['Titolo', 'Artista', 'Produttore (Label)', 'Anno', 'Codice ISRC', 'Numero di passaggi totali nel mese', 'Minuti totali di trasmissione']
                for col_num, header in enumerate(headers):
                    worksheet.write(0, col_num, header)
                    
                for row_num, row in enumerate(rows, start=1):
                    minuti = round(row['secondi'] / 60.0, 2)
                    worksheet.write(row_num, 0, row['titolo_pulito'])
                    worksheet.write(row_num, 1, row['artista_pulito'])
                    worksheet.write(row_num, 2, row['casa_discografica'] or '')
                    worksheet.write(row_num, 3, row['anno_pubblicazione'] or '')
                    worksheet.write(row_num, 4, row['codice_isrc'] or '')
                    worksheet.write(row_num, 5, row['passaggi'])
                    worksheet.write(row_num, 6, minuti)
                    
                workbook.close()
                xlsx_data = output.getvalue()
                
                filename = f"report_scf_{radio_id or 'tutte'}_{month}.xlsx"
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
                self.end_headers()
                self.wfile.write(xlsx_data)
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                print(f"Errore export SCF: {e}")
            return

        # 4. Report LEA / Soundreef (CSV)
        elif path == '/api/export/lea':
            month = query.get('month', [''])[0]
            radio_id = query.get('radio_id', [None])[0]
            if radio_id == 'all' or not radio_id:
                radio_id = None
                
            if not month:
                self.send_response(400)
                self.end_headers()
                return
                
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                sql = '''
                SELECT 
                    p.data, 
                    p.ora, 
                    p.durata, 
                    p.titolo, 
                    p.artista, 
                    m.codice_iswc, 
                    m.autore,
                    m.compositore
                FROM passaggi p
                LEFT JOIN canzoni_metadati m ON p.artista_pulito = m.artista_pulito AND p.titolo_pulito = m.titolo_pulito
                WHERE p.data >= ? AND p.data < ?
                '''
                params = list(month_range(month))
                if radio_id:
                    sql += " AND p.id_radio = ?"
                    params.append(radio_id)
                sql += " ORDER BY p.data ASC, p.ora ASC"
                
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                conn.close()
                
                output = io.StringIO()
                writer = csv.writer(output, delimiter=';')
                
                writer.writerow(['Data', 'Ora inizio', 'Durata (sec)', 'Titolo', 'Artista', 'Codice ISWC', 'Autori'])
                
                for row in rows:
                    authors = ", ".join(filter(None, [row['autore'], row['compositore']]))
                    writer.writerow([
                        row['data'],
                        row['ora'],
                        row['durata'],
                        row['titolo'],
                        row['artista'],
                        row['codice_iswc'] or '',
                        authors
                    ])
                    
                csv_data = output.getvalue().encode('utf-8')
                filename = f"report_lea_{radio_id or 'tutte'}_{month}.csv"
                
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'text/csv; charset=utf-8')
                self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
                self.end_headers()
                self.wfile.write(csv_data)
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                print(f"Errore export LEA: {e}")
            return

        # 5. Report SIAE (Fixed Width TXT)
        elif path == '/api/export/siae':
            month = query.get('month', [''])[0]
            radio_id = query.get('radio_id', [None])[0]
            if radio_id == 'all' or not radio_id:
                radio_id = None
                
            if not month:
                self.send_response(400)
                self.end_headers()
                return
                
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                sql = '''
                SELECT 
                    p.data, 
                    p.ora, 
                    p.durata, 
                    p.titolo, 
                    p.artista, 
                    m.codice_siae,
                    m.codice_iswc, 
                    m.autore,
                    m.compositore
                FROM passaggi p
                LEFT JOIN canzoni_metadati m ON p.artista_pulito = m.artista_pulito AND p.titolo_pulito = m.titolo_pulito
                WHERE p.data >= ? AND p.data < ?
                '''
                params = list(month_range(month))
                if radio_id:
                    sql += " AND p.id_radio = ?"
                    params.append(radio_id)
                sql += " ORDER BY p.data ASC, p.ora ASC"
                
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                conn.close()
                
                lines = []
                for row in rows:
                    d_iso = row['data']
                    try:
                        dp = d_iso.split('-')
                        d_siae = f"{dp[2]}/{dp[1]}/{dp[0]}"
                    except:
                        d_siae = d_iso
                        
                    authors = ", ".join(filter(None, [row['autore'], row['compositore']]))
                    
                    # Sanitizzazione dei caratteri speciali e accentati per la SIAE
                    title_sanitized = sanitize_for_siae(row['titolo'])
                    artist_sanitized = sanitize_for_siae(row['artista'])
                    authors_sanitized = sanitize_for_siae(authors)
                    
                    date_field = f"{d_siae:<10}"[:10]
                    time_field = f"{row['ora']:<8}"[:8]
                    title_field = f"{title_sanitized:<40}"[:40]
                    artist_field = f"{artist_sanitized:<40}"[:40]
                    siae_field = f"{(row['codice_siae'] or ''):<10}"[:10]
                    iswc_field = f"{(row['codice_iswc'] or ''):<15}"[:15]
                    auth_field = f"{authors_sanitized:<40}"[:40]
                    dur_field = f"{str(row['durata']):>6}"[:6]
                    
                    record_line = f"{date_field}{time_field}{title_field}{artist_field}{siae_field}{iswc_field}{auth_field}{dur_field}"
                    lines.append(record_line)
                    
                txt_data = "\r\n".join(lines).encode('utf-8')
                filename = f"report_siae_{radio_id or 'tutte'}_{month}.txt"
                
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'text/plain; charset=utf-8')
                self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
                self.end_headers()
                self.wfile.write(txt_data)
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                print(f"Errore export SIAE: {e}")
            return
            
        else:
            # Fallback static files serving
            super().do_GET()

    def do_POST(self):
        # 1. API esistente: Override manuale da classifica_radio.html
        if self.path == '/api/override':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                artist = data.get('artist')
                title = data.get('title')
                year = data.get('year')
                radio_date = data.get('radioDate')
                
                if not artist or not title or year is None or radio_date is None:
                    raise ValueError("Dati mancanti (richiesti artist, title, year, radioDate)")
                
                key = f"{artist} - {title}"
                
                # 1. Gestione Anno di Pubblicazione
                override_file = os.path.join(DIRECTORY, 'manual_years_override.json')
                overrides = {}
                if os.path.exists(override_file):
                    with open(override_file, 'r', encoding='utf-8') as f:
                        try:
                            overrides = json.load(f)
                        except Exception as e:
                            print(f"Errore caricamento override anno: {e}")
                            overrides = {}
                
                if year == 'N/A' or not year.strip():
                    if key in overrides:
                        del overrides[key]
                        print(f"Rimosso override manuale anno per: {key}")
                else:
                    overrides[key] = year.strip()
                    print(f"Impostato override manuale anno per: {key} -> {year}")
                
                with open(override_file, 'w', encoding='utf-8') as f:
                    json.dump(overrides, f, indent=2, ensure_ascii=False)

                # 2. Gestione Radio Date
                radiodate_override_file = os.path.join(DIRECTORY, 'manual_radiodates_override.json')
                radiodate_overrides = {}
                if os.path.exists(radiodate_override_file):
                    with open(radiodate_override_file, 'r', encoding='utf-8') as f:
                        try:
                            radiodate_overrides = json.load(f)
                        except Exception as e:
                            print(f"Errore caricamento override radio date: {e}")
                            radiodate_overrides = {}
                
                if radio_date == 'N/A' or not radio_date.strip():
                    if key in radiodate_overrides:
                        del radiodate_overrides[key]
                        print(f"Rimosso override manuale radio date per: {key}")
                else:
                    radiodate_overrides[key] = radio_date.strip()
                    print(f"Impostato override manuale radio date per: {key} -> {radio_date}")
                
                with open(radiodate_override_file, 'w', encoding='utf-8') as f:
                    json.dump(radiodate_overrides, f, indent=2, ensure_ascii=False)
                
                # Aggiorna anche centralmente in SQLite
                art_c, tit_c = clean_song(artist, title)
                update_metadata(
                    artist_clean=art_c,
                    title_clean=tit_c,
                    siae='',
                    iswc='',
                    isrc='',
                    compositore='',
                    autore='',
                    label='',
                    year=year.strip() if year and year != 'N/A' else ''
                )
                
                print("Rigenerazione classifica_radio.html in corso...")
                creation_flags = 0
                if sys.platform == 'win32':
                    creation_flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)
                
                result = subprocess.run(
                    [sys.executable, 'genera_html.py'], 
                    cwd=DIRECTORY, 
                    capture_output=True, 
                    text=True,
                    creationflags=creation_flags
                )
                
                if result.returncode == 0:
                    print("Rigenerazione completata con successo!")
                    self.send_response(200)
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": True}).encode('utf-8'))
                else:
                    print(f"Errore durante genera_html.py:\n{result.stderr}")
                    self.send_response(500)
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": False, "error": f"Errore rigenerazione HTML: {result.stderr}"}).encode('utf-8'))
                
            except Exception as e:
                print(f"Errore API override: {e}")
                self.send_response(400)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))
            return

        # 2. API esistente: Ricerca online canzone da classifica_radio.html
        elif self.path == '/api/search':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                artist = data.get('artist')
                title = data.get('title')
                
                if not artist or not title:
                    raise ValueError("Dati mancanti (richiesti artist e title)")
                
                print(f"Ricerca online dati canzone per: {artist} - {title}...")
                year = find_year(artist, title)
                radio_date = find_radio_date(artist, title)
                
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "year": year,
                    "radioDate": radio_date
                }).encode('utf-8'))
            except Exception as e:
                print(f"Errore API search: {e}")
                self.send_response(400)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))
            return

        # 3. API Nuova: Aggiornamento metadati dal dashboard
        elif self.path == '/api/metadata/update':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                artist_clean = data.get('artista_pulito')
                title_clean = data.get('titolo_pulito')
                
                if not artist_clean or not title_clean:
                    raise ValueError("Dati artista_pulito e titolo_pulito obbligatori")
                    
                values = {field: str(data.get(field, '') or '').strip() for field in METADATA_FIELDS}
                update_metadata(
                    artist_clean=artist_clean,
                    title_clean=title_clean,
                    siae=values['codice_siae'],
                    iswc=values['codice_iswc'],
                    isrc=values['codice_isrc'],
                    compositore=values['compositore'],
                    autore=values['autore'],
                    label=values['casa_discografica'],
                    year=values['anno_pubblicazione']
                )
                update_cached_song(artist_clean, title_clean, values)

                song = apply_song_status(dict(values, artista_pulito=artist_clean, titolo_pulito=title_clean))
                self.send_json({"success": True, "song": song})

                # Invia a Google Sheets solo questo brano (in background, raggruppato)
                queue_sheets_push(artist_clean, title_clean)
            except Exception as e:
                self.send_response(400)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))
            return

        # API: Ricerca online dei metadati di un singolo brano (non salva, propone)
        elif self.path == '/api/song/lookup':
            try:
                data = self.read_json_body()
                artist_clean = data.get('artista_pulito')
                title_clean = data.get('titolo_pulito')
                if not artist_clean or not title_clean:
                    raise ValueError("Dati artista_pulito e titolo_pulito obbligatori")
                self.send_json({"success": True, "found": lookup_song_online(artist_clean, title_clean, data.get('codice_isrc'))})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, 400)
            return

        # 4. API Nuova: Importazione log proprietari MB Studio / DJ Pro
        elif self.path == '/api/import_log':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                radio_id = data.get('radio_id')
                file_content = data.get('file_content')
                
                if not radio_id or not file_content:
                    raise ValueError("Parametri radio_id e file_content richiesti")
                    
                count = parse_log_file(file_content, radio_id)
                invalidate_songs_cache()

                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "count": count}).encode('utf-8'))
            except Exception as e:
                self.send_response(400)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))
            return

        # 5. API Nuova: Avvio scraper retroattivo per data e radio specifica
        elif self.path == '/api/scrape_retro':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                radio_id = data.get('radio_id')
                date_str = data.get('date')
                
                if not radio_id or not date_str:
                    raise ValueError("Parametri radio_id e date (YYYY-MM-DD) richiesti")
                    
                success, msg = scrape_retro(radio_id, date_str)
                invalidate_songs_cache()

                self.send_response(200 if success else 400)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": success, "message": msg}).encode('utf-8'))
            except Exception as e:
                self.send_response(400)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))
            return

        # 6. API Nuova: Avvio arricchimento canzoni in background (ottimizzato per frequenza)
        elif self.path == '/api/run_enrichment':
            try:
                import threading
                from bulk_enrichment import run_bulk_enrichment
                
                limit = 500
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0:
                    post_data = self.rfile.read(content_length)
                    try:
                        data = json.loads(post_data.decode('utf-8'))
                        limit = int(data.get('limit', 500))
                    except:
                        pass
                
                # Esegui il worker bulk in background per il limite specificato
                t = threading.Thread(target=run_bulk_enrichment, kwargs={"limit": limit, "max_threads": 10})
                t.start()
                
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "message": f"Arricchimento ottimizzato avviato in background per {limit} canzoni."}).encode('utf-8'))
            except Exception as e:
                self.send_response(400)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))
            return

        # 7. API Nuova: Sincronizzazione metadati con Google Sheets in background
        elif self.path == '/api/sheets/sync':
            try:
                import threading
                from google_sheets_sync import sync_metadata
                
                t = threading.Thread(target=sync_metadata)
                t.start()
                
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "message": "Sincronizzazione con Google Sheets avviata in background."}).encode('utf-8'))
            except Exception as e:
                self.send_response(400)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))
            return

        else:
            self.send_response(404)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

class ThreadingServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    # Ogni richiesta in un thread: scraper e ricerche online non bloccano più la dashboard
    daemon_threads = True
    allow_reuse_address = True

if __name__ == "__main__":
    try:
        init_db()  # crea tabelle e indici mancanti (il primo avvio può richiedere qualche secondo)
    except Exception as e:
        print(f"Errore inizializzazione database: {e}")
    # L'arricchimento gira dentro questo processo: uno stato "running" rimasto nel file
    # all'avvio è di un'esecuzione interrotta, e terrebbe la barra di avanzamento sempre visibile
    progress_file = os.path.join(DIRECTORY, 'scratch', 'enrichment_progress.json')
    try:
        with open(progress_file, 'r', encoding='utf-8') as f:
            progress = json.load(f)
        if progress.get("status") == "running":
            progress["status"] = "interrupted"
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress, f, indent=2)
    except Exception:
        pass
    try:
        with ThreadingServer(("", PORT), MyHandler) as httpd:
            print(f"\n========================================================")
            print(f"  [SERVER] SERVER INTERFACCIA WEB & REPORT ATTIVO!")
            print(f"  [SERVER] Dashboard: http://localhost:{PORT}/dashboard.html")
            print(f"  [SERVER] Classifiche: http://localhost:{PORT}/classifica_radio.html")
            print(f"========================================================")
            print("  Premi Ctrl+C per spegnere il server.\n")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nSpegnimento del server locale.")
    except Exception as e:
        print(f"Errore all'avvio del server: {e}")
