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

from db_manager import get_db_connection, update_metadata, get_monthly_unique_songs, insert_passage
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

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

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
            radios_list = [
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
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(radios_list).encode('utf-8'))
            return

        # 2. API: Dati Dashboard
        elif path == '/api/dashboard_data':
            month = query.get('month', [''])[0] # YYYY-MM
            radio_id = query.get('radio_id', [None])[0]
            if radio_id == 'all' or not radio_id:
                radio_id = None
                
            if not month:
                self.send_response(400)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": "Parametro month richiesto (YYYY-MM)"}).encode('utf-8'))
                return
                
            try:
                songs = get_monthly_unique_songs(month, radio_id)
                songs_list = []
                
                stats = {"total": 0, "green": 0, "yellow": 0, "red": 0}
                
                for row in songs:
                    siae = row["codice_siae"] or ""
                    iswc = row["codice_iswc"] or ""
                    isrc = row["codice_isrc"] or ""
                    composer = row["compositore"] or ""
                    author = row["autore"] or ""
                    label = row["casa_discografica"] or ""
                    year = row["anno_pubblicazione"] or ""
                    
                    # Helper per verificare se un campo è effettivamente vuoto
                    def is_empty(val):
                        return not val or val.strip() in ['', '-', 'N/A', 'N/D']

                    has_siae = not is_empty(siae)
                    has_isrc = not is_empty(isrc)
                    has_iswc = not is_empty(iswc)
                    has_writer = not (is_empty(composer) and is_empty(author))
                    has_label_or_year = not (is_empty(label) and is_empty(year))
                    
                    if (has_siae or has_iswc) and has_isrc and has_writer and has_label_or_year:
                        status = "green"
                        stats["green"] += 1
                    elif not has_siae and not has_iswc and not has_isrc and not has_writer and not has_label_or_year:
                        status = "red"
                        stats["red"] += 1
                    else:
                        status = "yellow"
                        stats["yellow"] += 1
                        
                    stats["total"] += 1
                    
                    songs_list.append({
                        "artista_pulito": row["artista_pulito"],
                        "titolo_pulito": row["titolo_pulito"],
                        "codice_siae": siae,
                        "codice_iswc": iswc,
                        "codice_isrc": isrc,
                        "compositore": composer,
                        "autore": author,
                        "casa_discografica": label,
                        "anno_pubblicazione": year,
                        "status": status
                    })
                    
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "songs": songs_list, "stats": stats}).encode('utf-8'))
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))
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
                WHERE p.data LIKE ?
                '''
                params = [f"{month}%"]
                if radio_id:
                    sql += " AND p.id_radio = ?"
                    params.append(radio_id)
                sql += " GROUP BY p.artista_pulito, p.titolo_pulito ORDER BY passaggi DESC"
                
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                conn.close()
                
                output = io.BytesIO()
                workbook = xlsxwriter.Workbook(output)
                worksheet = workbook.add_sheet('Report SCF')
                
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
                WHERE p.data LIKE ?
                '''
                params = [f"{month}%"]
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
                WHERE p.data LIKE ?
                '''
                params = [f"{month}%"]
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
                    
                update_metadata(
                    artist_clean=artist_clean,
                    title_clean=title_clean,
                    siae=data.get('codice_siae', ''),
                    iswc=data.get('codice_iswc', ''),
                    isrc=data.get('codice_isrc', ''),
                    compositore=data.get('compositore', ''),
                    autore=data.get('autore', ''),
                    label=data.get('casa_discografica', ''),
                    year=data.get('anno_pubblicazione', '')
                )
                
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True}).encode('utf-8'))
                
                # Sincronizza con Google Sheets in background
                try:
                    import threading
                    from google_sheets_sync import sync_metadata
                    t = threading.Thread(target=sync_metadata)
                    t.start()
                except Exception as ex:
                    print(f"Errore avvio sync Sheets: {ex}")
            except Exception as e:
                self.send_response(400)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))
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

if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
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
