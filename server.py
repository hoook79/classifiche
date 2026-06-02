#!/usr/bin/env python3
import http.server
import socketserver
import json
import os
import subprocess
import sys

# Forza il reindirizzamento di stdout e stderr su log file per catturare qualsiasi errore in background
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
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
    # Fallback estremo se il file non è scrivibile
    devnull = open(os.devnull, 'w')
    sys.stdout = devnull
    sys.stderr = devnull

PORT = 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

def find_year(artist, title):
    song_query = f"{artist} - {title}"
    try:
        sys.path.append(DIRECTORY)
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
        sys.path.append(DIRECTORY)
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

    def do_POST(self):
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
                
                # Rigenera la pagina HTML
                print("Rigenerazione classifica_radio.html in corso...")
                # Esegui genera_html.py come sottoprocesso in modo silenzioso (senza far apparire finestre DOS)
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
                    # Invia risposta OK
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
        else:
            self.send_response(404)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

if __name__ == "__main__":
    # Avvia il server
    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
            print(f"\n========================================================")
            print(f"  [SERVER] SERVER INTERFACCIA WEB ATTIVO!")
            print(f"  [SERVER] Apri nel browser: http://localhost:{PORT}/classifica_radio.html")
            print(f"========================================================")
            print("  Tieni questa finestra aperta per consentire le modifiche online.")
            print("  Premi Ctrl+C in questa finestra per spegnere il server.\n")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nSpegnimento del server locale.")
    except Exception as e:
        print(f"Errore all'avvio del server: {e}")
