#!/usr/bin/env python3
import os
import sys
import json
import time
import re
import difflib
import urllib.parse
import requests
import threading
from db_manager import get_db_connection, update_metadata

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except Exception as e:
                print(f"Errore caricamento config.json: {e}")
    return {}

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def get_spotify_token(client_id, client_secret):
    """Richiede il token di accesso a Spotify tramite Client Credentials Flow."""
    if not client_id or not client_secret:
        return None
    url = "https://accounts.spotify.com/api/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {"grant_type": "client_credentials"}
    try:
        r = requests.post(url, headers=headers, data=data, auth=(client_id, client_secret), timeout=10)
        if r.status_code == 200:
            return r.json().get("access_token")
        else:
            print(f"[SPOTIFY] Errore token: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"[SPOTIFY] Errore richiesta token: {e}")
    return None

def search_spotify(artist, title, token):
    """
    Cerca il brano su Spotify. Ritorna (isrc, anno, label).
    """
    if not token:
        return None, None, None
        
    query = f'artist:"{artist}" track:"{title}"'
    encoded_query = urllib.parse.quote(query)
    url = f"https://api.spotify.com/v1/search?q={encoded_query}&type=track&limit=1"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            print(f"[SPOTIFY] Errore di ricerca: {r.status_code}")
            return None, None, None
            
        data = r.json()
        tracks = data.get("tracks", {}).get("items", [])
        if not tracks:
            # Riprova con una ricerca meno restrittiva
            query_simple = f'{artist} {title}'
            encoded_query_simple = urllib.parse.quote(query_simple)
            url_simple = f"https://api.spotify.com/v1/search?q={encoded_query_simple}&type=track&limit=1"
            r = requests.get(url_simple, headers=headers, timeout=10)
            if r.status_code == 200:
                tracks = r.json().get("tracks", {}).get("items", [])
                
        if tracks:
            track = tracks[0]
            isrc = track.get("external_ids", {}).get("isrc")
            
            # Estrai anno
            release_date = track.get("album", {}).get("release_date", "")
            year = release_date.split("-")[0] if release_date else None
            
            # Per ottenere l'etichetta (label), dobbiamo interrogare l'album
            album_id = track.get("album", {}).get("id")
            label = None
            if album_id:
                # Piccolo delay per non saturare Spotify
                time.sleep(0.1)
                album_url = f"https://api.spotify.com/v1/albums/{album_id}"
                album_r = requests.get(album_url, headers=headers, timeout=10)
                if album_r.status_code == 200:
                    label = album_r.json().get("label")
            
            return isrc, year, label
    except Exception as e:
        print(f"[SPOTIFY] Eccezione durante la ricerca: {e}")
        
    return None, None, None

# Cache globale degli album per Deezer per evitare chiamate di rete duplicate
DEEZER_ALBUM_CACHE = {}
album_cache_lock = threading.Lock() if 'threading' in sys.modules else None
if not album_cache_lock:
    import threading
    album_cache_lock = threading.Lock()

def get_deezer_album_details(album_id):
    if not album_id:
        return None, None
    with album_cache_lock:
        if album_id in DEEZER_ALBUM_CACHE:
            return DEEZER_ALBUM_CACHE[album_id]
            
    url = f"https://api.deezer.com/album/{album_id}"
    try:
        time.sleep(0.05)
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            label = data.get("label")
            rel_date = data.get("release_date")
            year = rel_date.split("-")[0] if rel_date else None
            
            with album_cache_lock:
                DEEZER_ALBUM_CACHE[album_id] = (year, label)
            return year, label
    except Exception as e:
        print(f"[DEEZER] Errore dettagli album {album_id}: {e}")
    return None, None

def is_fuzzy_match(artist_query, title_query, artist_result, title_result):
    """
    Verifica se il risultato trovato assomiglia alla query cercata.
    """
    def get_words(text):
        if not text:
            return set()
        return set(re.findall(r'\w+', text.lower()))
        
    q_art_words = get_words(artist_query)
    q_ttl_words = get_words(title_query)
    
    r_art_words = get_words(artist_result)
    r_ttl_words = get_words(title_result)
    
    def filter_short(words):
        filtered = {w for w in words if len(w) >= 3}
        return filtered if filtered else words
        
    q_art_long = filter_short(q_art_words)
    q_ttl_long = filter_short(q_ttl_words)
    
    art_ok = len(q_art_long.intersection(r_art_words)) >= 1 if q_art_long else True
    ttl_ok = len(q_ttl_long.intersection(r_ttl_words)) >= 1 if q_ttl_long else True
    
    return art_ok and ttl_ok

def search_deezer(artist, title):
    """
    Cerca il brano su Deezer. Ritorna (isrc, anno, label).
    Nessuna credenziale richiesta, limite rate molto alto.
    """
    query = f'track:"{title}" artist:"{artist}"'
    encoded_query = urllib.parse.quote(query)
    url = f"https://api.deezer.com/search?q={encoded_query}"
    
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return None, None, None
            
        items = r.json().get("data", [])
        is_fallback = False
        
        if not items:
            # Ricerca semplice fallback
            query_simple = f"{artist} {title}"
            encoded_query_simple = urllib.parse.quote(query_simple)
            url_simple = f"https://api.deezer.com/search?q={encoded_query_simple}"
            r = requests.get(url_simple, timeout=10)
            if r.status_code == 200:
                items = r.json().get("data", [])
                is_fallback = True
                
        if items:
            # Se è fallback, validiamo con fuzzy match
            valid_track = None
            if is_fallback:
                for item in items[:3]:  # Controlla i primi 3 risultati
                    res_artist = item.get("artist", {}).get("name", "")
                    res_title = item.get("title", "")
                    if is_fuzzy_match(artist, title, res_artist, res_title):
                        valid_track = item
                        break
            else:
                valid_track = items[0]
                
            if valid_track:
                isrc = valid_track.get("isrc")
                album_id = valid_track.get("album", {}).get("id")
                
                year = None
                label = None
                
                if album_id:
                    year, label = get_deezer_album_details(album_id)
                        
                return isrc, year, label
    except Exception as e:
        print(f"[DEEZER] Eccezione durante la ricerca di '{artist} - {title}': {e}")
        
    return None, None, None


# Cache globale per gli album di iTunes per evitare chiamate di rete duplicate
ITUNES_ALBUM_CACHE = {}
itunes_album_lock = threading.Lock() if 'threading' in sys.modules else None
if not itunes_album_lock:
    import threading
    itunes_album_lock = threading.Lock()

def get_itunes_album_details(album_id):
    if not album_id:
        return None, None
    with itunes_album_lock:
        if album_id in ITUNES_ALBUM_CACHE:
            return ITUNES_ALBUM_CACHE[album_id]
            
    url = f"https://itunes.apple.com/lookup?id={album_id}"
    try:
        time.sleep(0.05)
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            results = r.json().get("results", [])
            if results:
                album = results[0]
                copyright_str = album.get("copyright", "")
                label = copyright_str
                if copyright_str:
                    label = re.sub(r'℗\s*\d{4}\s*', '', copyright_str).strip()
                    label = re.sub(r'©\s*\d{4}\s*', '', label).strip()
                
                rel_date = album.get("releaseDate")
                year = rel_date.split("-")[0] if rel_date else None
                
                with itunes_album_lock:
                    ITUNES_ALBUM_CACHE[album_id] = (year, label)
                return year, label
    except Exception as e:
        print(f"[ITUNES] Errore dettagli album {album_id}: {e}")
    return None, None

def search_itunes(artist, title):
    """
    Cerca la canzone su iTunes. Ritorna (anno, label).
    """
    query = f"{artist} {title}"
    encoded_query = urllib.parse.quote(query)
    url = f"https://itunes.apple.com/search?term={encoded_query}&media=music&limit=1"
    
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            results = r.json().get("results", [])
            if results:
                track = results[0]
                album_id = track.get("collectionId")
                
                year = None
                label = None
                
                if album_id:
                    year, label = get_itunes_album_details(album_id)
                else:
                    rel_date = track.get("releaseDate")
                    year = rel_date.split("-")[0] if rel_date else None
                    
                return year, label
    except Exception as e:
        print(f"[ITUNES] Errore ricerca '{artist} - {title}': {e}")
    return None, None


MB_HEADERS = {"User-Agent": "BroadcasterReportsApp/1.0.0 ( contact@broadcaster-reports.it )"}

def _mb_get(url):
    """GET su MusicBrainz rispettando il limite di 1 richiesta al secondo."""
    time.sleep(1.1)
    r = requests.get(url, headers=MB_HEADERS, timeout=10)
    if r.status_code != 200:
        return None
    return r.json()

def _norm_title(text):
    # Ignora le parti tra parentesi (feat., versioni) e la punteggiatura
    text = re.sub(r'[\(\[].*?[\)\]]', ' ', (text or '').lower())
    text = re.sub(r'\b(feat|ft)\b.*$', ' ', text)
    return " ".join(re.findall(r'\w+', text))

def is_same_recording(artist_query, title_query, artist_result, title_result):
    """Verifica stretta: titolo quasi identico e almeno un nome di artista in comune."""
    t_q, t_r = _norm_title(title_query), _norm_title(title_result)
    if not t_q or not t_r:
        return False
    if difflib.SequenceMatcher(None, t_q, t_r).ratio() < 0.85:
        return False
    a_q = {w for w in re.findall(r'\w+', (artist_query or '').lower()) if len(w) >= 3}
    a_r = set(re.findall(r'\w+', (artist_result or '').lower()))
    return not a_q or bool(a_q & a_r)

def _work_credits(work_id):
    """Ritorna (iswc, compositori, autori) di un'opera MusicBrainz."""
    work = _mb_get(f"https://musicbrainz.org/ws/2/work/{work_id}?inc=artist-rels&fmt=json")
    if not work:
        return None, [], []
    composers, lyricists = [], []
    for rel in work.get("relations", []):
        if rel.get("target-type") != "artist":
            continue
        name = rel.get("artist", {}).get("name")
        rel_type = rel.get("type")
        if rel_type in ("composer", "writer") and name not in composers:
            composers.append(name)
        if rel_type in ("lyricist", "writer") and name not in lyricists:
            lyricists.append(name)
    iswcs = work.get("iswcs") or []
    return (iswcs[0] if iswcs else None), composers, lyricists

def _credits_from_recording(recording):
    """Segue i collegamenti registrazione -> opera e ne legge ISWC e autori."""
    for rel in recording.get("relations", []):
        if rel.get("target-type") == "work" and rel.get("work", {}).get("id"):
            iswc, composers, lyricists = _work_credits(rel["work"]["id"])
            if iswc or composers or lyricists:
                return iswc, composers, lyricists
    return None, [], []

def _as_result(iswc, composers, lyricists):
    return iswc, (", ".join(composers) if composers else None), (", ".join(lyricists) if lyricists else None)

def search_musicbrainz(artist, title, isrc=None):
    """
    Cerca ISWC e autori di un brano su MusicBrainz. Ritorna (iswc, compositori, autori).
    1. Se c'è l'ISRC: identifica la registrazione esatta e ne segue l'opera.
    2. Altrimenti (o se l'ISRC non porta a un'opera): ricerca per testo, accettando solo
       risultati con titolo quasi identico e artista in comune, provando più candidati.
    Rispettare il limite di 1 req/sec (ogni richiesta attende 1.1s).
    """
    try:
        if isrc and str(isrc).strip() not in ('', '-', 'N/A', 'N/D'):
            data = _mb_get(f"https://musicbrainz.org/ws/2/isrc/{urllib.parse.quote(str(isrc).strip())}?inc=work-rels&fmt=json")
            for recording in (data or {}).get("recordings", []):
                iswc, composers, lyricists = _credits_from_recording(recording)
                if iswc or composers or lyricists:
                    return _as_result(iswc, composers, lyricists)

        query = urllib.parse.quote(f'artist:"{artist}" AND recording:"{_norm_title(title) or title}"')
        data = _mb_get(f"https://musicbrainz.org/ws/2/recording/?query={query}&limit=15&fmt=json")
        candidates = []
        for rec in (data or {}).get("recordings", []):
            rec_artist = " ".join(c.get("name", "") + " " + c.get("artist", {}).get("name", "") for c in rec.get("artist-credit", []))
            if is_same_recording(artist, title, rec_artist, rec.get("title")):
                candidates.append(rec)

        # Le registrazioni collegate a un'opera sono poche: ne proviamo al massimo 3
        for rec in candidates[:3]:
            details = _mb_get(f"https://musicbrainz.org/ws/2/recording/{rec['id']}?inc=work-rels&fmt=json")
            if not details:
                continue
            iswc, composers, lyricists = _credits_from_recording(details)
            if iswc or composers or lyricists:
                return _as_result(iswc, composers, lyricists)
    except Exception as e:
        print(f"[MUSICBRAINZ] Errore durante la ricerca: {e}")

    return None, None, None

def run_enrichment(limit=50):
    """
    Trova canzoni senza codici legali ed esegue l'arricchimento.
    """
    config = load_config()
    spotify_client_id = config.get("spotify_client_id")
    spotify_client_secret = config.get("spotify_client_secret")
    
    spotify_token = None
    if spotify_client_id and spotify_client_secret:
        print("[SPOTIFY] Autenticazione in corso...")
        spotify_token = get_spotify_token(spotify_client_id, spotify_client_secret)
        if spotify_token:
            print("[SPOTIFY] Autenticato correttamente.")
        else:
            print("[SPOTIFY] Autenticazione fallita. Il servizio Spotify verrà saltato.")
    else:
        print("[SPOTIFY] Credenziali non fornite in config.json. Il servizio Spotify verrà saltato.")
        
    # Trova brani nel DB senza metadati popolati
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT artista_pulito, titolo_pulito, codice_siae, codice_iswc, codice_isrc, compositore, autore, casa_discografica, anno_pubblicazione
    FROM canzoni_metadati
    WHERE (codice_iswc IS NULL OR codice_iswc = '')
       OR (codice_isrc IS NULL OR codice_isrc = '')
       OR (compositore IS NULL OR compositore = '')
    LIMIT ?
    ''', (limit,))
    
    songs = cursor.fetchall()
    conn.close()
    
    if not songs:
        print("Nessuna canzone da arricchire presente nel database.")
        return
        
    print(f"Trovate {len(songs)} canzoni da arricchire. Avvio elaborazione...")
    
    success_count = 0
    for song in songs:
        artist = song["artista_pulito"]
        title = song["titolo_pulito"]
        
        current_siae = song["codice_siae"] or ""
        current_iswc = song["codice_iswc"] or ""
        current_isrc = song["codice_isrc"] or ""
        current_composer = song["compositore"] or ""
        current_author = song["autore"] or ""
        current_label = song["casa_discografica"] or ""
        current_year = song["anno_pubblicazione"] or ""
        
        print(f"\n[WORKER] Canzone: '{artist} - {title}'")
        
        # 1. Ricerca Spotify (ISRC, Anno, Label)
        isrc, year, label = None, None, None
        if spotify_token:
            print("  Interrogazione Spotify...")
            isrc, year, label = search_spotify(artist, title, spotify_token)
            if isrc or year or label:
                print(f"    Trovato da Spotify: ISRC={isrc}, Anno={year}, Label={label}")
                
        # Fallback automatico su Deezer se Spotify non ha trovato codici o non è configurato
        if not isrc or not label or not year:
            print("  Interrogazione Deezer...")
            d_isrc, d_year, d_label = search_deezer(artist, title)
            if d_isrc or d_year or d_label:
                print(f"    Trovato da Deezer: ISRC={d_isrc}, Anno={d_year}, Label={d_label}")
                isrc = isrc or d_isrc
                year = year or d_year
                label = label or d_label
                
        # Fallback automatico su iTunes se mancano ancora anno o label
        if not year or not label:
            print("  Interrogazione iTunes...")
            it_year, it_label = search_itunes(artist, title)
            if it_year or it_label:
                print(f"    Trovato da iTunes: Anno={it_year}, Label={it_label}")
                year = year or it_year
                label = label or it_label
                
        # 2. Ricerca MusicBrainz (ISWC, Compositori, Autori)
        print("  Interrogazione MusicBrainz...")
        iswc, composers, authors = search_musicbrainz(artist, title)
        if iswc or composers or authors:
            print(f"    Trovato da MusicBrainz: ISWC={iswc}, Compositori={composers}, Autori={authors}")
            
        # Unisci i dati (preferendo i nuovi se i vecchi erano vuoti)
        new_isrc = isrc if isrc else current_isrc
        new_year = str(year) if year else current_year
        new_label = label if label else current_label
        
        new_iswc = iswc if iswc else current_iswc
        new_composer = composers if composers else current_composer
        new_author = authors if authors else current_author
        
        # Aggiorna il database
        update_metadata(
            artist_clean=artist,
            title_clean=title,
            siae=current_siae, # Conserva codice SIAE se presente (viene inserito manualmente)
            iswc=new_iswc,
            isrc=new_isrc,
            compositore=new_composer,
            autore=new_author,
            label=new_label,
            year=new_year
        )
        
        success_count += 1
        
    print(f"\n[WORKER] Arricchimento completato per {success_count} canzoni.")

if __name__ == "__main__":
    # Crea un file config.json vuoto se non esiste per aiutare l'utente
    if not os.path.exists(CONFIG_FILE):
        save_config({
            "spotify_client_id": "",
            "spotify_client_secret": ""
        })
        print(f"Creato file di configurazione vuoto in {CONFIG_FILE}. Inserisci lì le credenziali di Spotify Developer per abilitare Spotify.")
        
    # Esegue l'arricchimento
    limit_val = 10
    if len(sys.argv) > 1:
        try:
            limit_val = int(sys.argv[1])
        except:
            pass
    run_enrichment(limit=limit_val)
