#!/usr/bin/env python3
import sys
import os
import time
import json
import sqlite3
import urllib.parse
import requests
import concurrent.futures
import threading

DIRECTORY = os.path.dirname(os.path.abspath(__file__))
sys.path.append(DIRECTORY)

from db_manager import get_db_connection, update_metadata
from enrichment_worker import load_config, get_spotify_token, search_spotify, search_deezer, search_itunes, search_musicbrainz

PROGRESS_FILE = os.path.join(DIRECTORY, 'scratch', 'enrichment_progress.json')

# Lock globali per la sincronizzazione tra thread
db_lock = threading.Lock()
musicbrainz_lock = threading.Lock()
progress_lock = threading.Lock()

last_musicbrainz_call_time = 0.0

# Stato del progresso
progress_state = {
    "status": "idle",
    "total": 0,
    "processed": 0,
    "success": 0,
    "started_at": 0.0,
    "elapsed": 0.0
}

def save_progress():
    os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)
    with progress_lock:
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(progress_state, f, indent=2)

def update_progress_processed(is_success=False):
    with progress_lock:
        progress_state["processed"] += 1
        if is_success:
            progress_state["success"] += 1
        progress_state["elapsed"] = round(time.time() - progress_state["started_at"], 2)
    save_progress()

def rate_limited_search_musicbrainz(artist, title):
    """
    Esegue la ricerca su MusicBrainz rispettando il rate limit globale di 1 req/sec.
    """
    global last_musicbrainz_call_time
    with musicbrainz_lock:
        now = time.time()
        elapsed = now - last_musicbrainz_call_time
        # Mantieni un margine di sicurezza di 1.2 secondi
        wait_time = 1.2 - elapsed
        if wait_time > 0:
            time.sleep(wait_time)
        last_musicbrainz_call_time = time.time()
        return search_musicbrainz(artist, title)

def process_single_song(song, spotify_token):
    """
    Elabora una singola canzone nei thread.
    """
    artist = song["artista_pulito"]
    title = song["titolo_pulito"]
    
    try:
        current_siae = song["codice_siae"] or ""
        current_iswc = song["codice_iswc"] or ""
        current_isrc = song["codice_isrc"] or ""
        current_composer = song["compositore"] or ""
        current_author = song["autore"] or ""
        current_label = song["casa_discografica"] or ""
        current_year = song["anno_pubblicazione"] or ""
        
        # 1. Ricerca Spotify (se abilitato)
        isrc, year, label = None, None, None
        if spotify_token:
            try:
                isrc, year, label = search_spotify(artist, title, spotify_token)
            except Exception as e:
                print(f"[THREAD-SPOTIFY] Errore per '{artist} - {title}': {e}")
                
        # 2. Fallback su Deezer (se Spotify non ha trovato tutto o è saltato)
        if not isrc or not label or not year:
            try:
                d_isrc, d_year, d_label = search_deezer(artist, title)
                isrc = isrc or d_isrc
                year = year or d_year
                label = label or d_label
            except Exception as e:
                print(f"[THREAD-DEEZER] Errore per '{artist} - {title}': {e}")
                
        # 3. Fallback su iTunes (se mancano ancora anno o label)
        if not year or not label:
            try:
                it_year, it_label = search_itunes(artist, title)
                year = year or it_year
                label = label or it_label
            except Exception as e:
                print(f"[THREAD-ITUNES] Errore per '{artist} - {title}': {e}")
                
        # 4. Ricerca MusicBrainz (per ISWC e Autori, solo se mancano e rispettando il rate limit)
        iswc, composers, authors = None, None, None
        needs_mb = (not current_iswc or current_iswc.strip() in ['', '-', 'N/A']) or \
                   (not current_composer or current_composer.strip() in ['', '-', 'N/A'])
                   
        if needs_mb:
            try:
                iswc, composers, authors = rate_limited_search_musicbrainz(artist, title)
            except Exception as e:
                print(f"[THREAD-MUSICBRAINZ] Errore per '{artist} - {title}': {e}")
                
        # Unione dati intelligente e sicura contro i tipi non stringa
        def clean_val(new_val, old_val):
            n_str = str(new_val).strip() if new_val is not None else ""
            o_str = str(old_val).strip() if old_val is not None else ""
            
            if n_str and n_str not in ['', '-', 'N/A', 'N/D']:
                return n_str
            if o_str and o_str not in ['', '-', 'N/A', 'N/D']:
                return o_str
            return ""
            
        new_isrc = clean_val(isrc, current_isrc)
        new_year = clean_val(year, current_year)
        new_label = clean_val(label, current_label)
        new_iswc = clean_val(iswc, current_iswc)
        new_composer = clean_val(composers, current_composer)
        new_author = clean_val(authors, current_author)
        
        # Aggiorna il database proteggendo la scrittura con un Lock
        has_new_info = False
        if new_isrc != current_isrc or new_year != current_year or new_label != current_label or \
           new_iswc != current_iswc or new_composer != current_composer or new_author != current_author:
            has_new_info = True
            
        with db_lock:
            try:
                update_metadata(
                    artist_clean=artist,
                    title_clean=title,
                    siae=current_siae,
                    iswc=new_iswc,
                    isrc=new_isrc,
                    compositore=new_composer,
                    autore=new_author,
                    label=new_label,
                    year=new_year
                )
            except Exception as e:
                print(f"[DB ERROR] Errore aggiornamento canzone '{artist} - {title}': {e}")
                
        # Logga il completamento
        status_str = "SUCCESSO" if has_new_info else "NESSUN NUOVO DATO"
        print(f"[ELABORATO] '{artist} - {title}' -> {status_str} (ISRC: {new_isrc or '-'}, ISWC: {new_iswc or '-'}, Anno: {new_year or '-'}, Label: {new_label or '-'})")
        
        update_progress_processed(is_success=has_new_info)
        
    except Exception as e:
        print(f"[CRITICAL THREAD ERROR] Errore imprevisto durante l'elaborazione di '{artist} - {title}': {e}")
        # Incrementa comunque processed per evitare blocchi del contatore progress
        update_progress_processed(is_success=False)

def run_bulk_enrichment(limit=500, max_threads=10):
    global progress_state
    print("========================================================")
    print("      AVVIO ARRICCHIMENTO IN BLOCCO MULTI-THREAD       ")
    print("========================================================")
    print(f"Configurazione: max {max_threads} thread paralleli, limite {limit} brani.\n")
    
    config = load_config()
    spotify_client_id = config.get("spotify_client_id")
    spotify_client_secret = config.get("spotify_client_secret")
    
    spotify_token = None
    if spotify_client_id and spotify_client_secret:
        print("[SPOTIFY] Richiesta token in corso...")
        spotify_token = get_spotify_token(spotify_client_id, spotify_client_secret)
        if spotify_token:
            print("[SPOTIFY] Autenticato correttamente.")
        else:
            print("[SPOTIFY] Autenticazione fallita. Spotify verrà saltato.")
            
    # 1. Recupera le canzoni ordinate per frequenza di trasmissione
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = '''
    SELECT 
        p.artista_pulito, 
        p.titolo_pulito, 
        COUNT(p.id) as play_count,
        m.codice_siae,
        m.codice_iswc,
        m.codice_isrc,
        m.compositore,
        m.autore,
        m.casa_discografica,
        m.anno_pubblicazione
    FROM passaggi p
    JOIN canzoni_metadati m ON p.artista_pulito = m.artista_pulito AND p.titolo_pulito = m.titolo_pulito
    WHERE (m.codice_iswc IS NULL OR m.codice_iswc = '' OR m.codice_iswc = '-')
       OR (m.codice_isrc IS NULL OR m.codice_isrc = '' OR m.codice_isrc = '-')
       OR (m.compositore IS NULL OR m.compositore = '' OR m.compositore = '-')
    GROUP BY p.artista_pulito, p.titolo_pulito
    ORDER BY play_count DESC
    LIMIT ?
    '''
    
    cursor.execute(query, (limit,))
    songs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    if not songs:
        print("Tutte le canzoni nel database sono già arricchite con successo!")
        # Azzera e imposta progress a idle
        progress_state = {
            "status": "idle",
            "total": 0,
            "processed": 0,
            "success": 0,
            "started_at": 0.0,
            "elapsed": 0.0
        }
        save_progress()
        return
        
    total_songs = len(songs)
    print(f"Trovate {total_songs} canzoni da elaborare. Inizio arricchimento parallelo...\n")
    
    # Inizializza lo stato del progresso
    progress_state = {
        "status": "running",
        "total": total_songs,
        "processed": 0,
        "success": 0,
        "started_at": time.time(),
        "elapsed": 0.0
    }
    save_progress()
    
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = [executor.submit(process_single_song, song, spotify_token) for song in songs]
            concurrent.futures.wait(futures)
    except KeyboardInterrupt:
        print("\n[INFO] Processo interrotto dall'utente. Dati salvati in sicurezza.")
        
    progress_state["status"] = "idle"
    save_progress()
    
    elapsed = round(time.time() - progress_state["started_at"], 2)
    print("\n========================================================")
    print(f"Arricchimento completato per {progress_state['processed']} canzoni (successi: {progress_state['success']}) in {elapsed} secondi.")
    print("========================================================")
    
    try:
        from google_sheets_sync import sync_metadata
        print("\n[GOOGLE SHEETS] Avvio sincronizzazione automatica dei metadati su Google Sheets...")
        sync_metadata()
    except Exception as e:
        print(f"[GOOGLE SHEETS] Impossibile avviare la sincronizzazione automatica: {e}")

if __name__ == "__main__":
    limit_val = 500
    threads_val = 10
    if len(sys.argv) > 1:
        try:
            limit_val = int(sys.argv[1])
        except:
            pass
    if len(sys.argv) > 2:
        try:
            threads_val = int(sys.argv[2])
        except:
            pass
            
    run_bulk_enrichment(limit=limit_val, max_threads=threads_val)
