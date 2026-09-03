#!/usr/bin/env python3
import os
import sqlite3
from data_cleaner import clean_song

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'radio_reports.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Crea Tabella Passaggi
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS passaggi (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_radio TEXT NOT NULL,
        data TEXT NOT NULL,          -- Formato: YYYY-MM-DD
        ora TEXT NOT NULL,           -- Formato: HH:MM:SS
        artista TEXT NOT NULL,       -- Artista originale
        titolo TEXT NOT NULL,        -- Titolo originale
        artista_pulito TEXT NOT NULL,-- Artista normalizzato
        titolo_pulito TEXT NOT NULL, -- Titolo normalizzato
        sorgente TEXT NOT NULL,      -- es: myradioonline, onlineradiobox, IMPORT_LOG, SCRAPER_RETRO
        durata INTEGER DEFAULT 240   -- Durata in secondi (default 4 minuti)
    )
    ''')
    
    # Crea Tabella Canzoni_Metadati
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS canzoni_metadati (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        artista_pulito TEXT NOT NULL,
        titolo_pulito TEXT NOT NULL,
        codice_siae TEXT DEFAULT '',
        codice_iswc TEXT DEFAULT '',
        codice_isrc TEXT DEFAULT '',
        compositore TEXT DEFAULT '',   -- Autore Musica
        autore TEXT DEFAULT '',        -- Autore Testo
        casa_discografica TEXT DEFAULT '', -- Label
        anno_pubblicazione TEXT DEFAULT '',
        UNIQUE(artista_pulito, titolo_pulito)
    )
    ''')
    
    # Indici per velocizzare le query
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_passaggi_radio_data ON passaggi(id_radio, data)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_passaggi_clean ON passaggi(artista_pulito, titolo_pulito)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_metadati_clean ON canzoni_metadati(artista_pulito, titolo_pulito)')
    
    conn.commit()
    conn.close()
    print("Database SQLite inizializzato correttamente.")

def insert_passage(id_radio, data_str, time_str, artist, title, source, duration=240):
    """
    Inserisce un passaggio. Pulisce artista e titolo per popolare anche i campi puliti
    e crea un record vuoto in canzoni_metadati se non esiste già.
    """
    # Normalizza data YYYY-MM-DD se DD-MM-YYYY
    if '-' in data_str and len(data_str.split('-')[0]) == 2:
        parts = data_str.split('-')
        data_str = f"{parts[2]}-{parts[1]}-{parts[0]}"
    elif '.' in data_str:
        # Gestisci formato DD.MM (assumiamo regola anno)
        parts = data_str.split('.')
        day = parts[0]
        month = parts[1]
        year = "2025" if int(month) >= 10 else "2026"
        data_str = f"{year}-{month}-{day}"
    
    # Normalizza ora in HH:MM:SS se HH:MM
    if len(time_str.split(':')) == 2:
        time_str = f"{time_str}:00"
        
    artist_clean, title_clean = clean_song(artist, title)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Inserisce il passaggio
    cursor.execute('''
    INSERT INTO passaggi (id_radio, data, ora, artista, titolo, artista_pulito, titolo_pulito, sorgente, durata)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (id_radio, data_str, time_str, artist, title, artist_clean, title_clean, source, duration))
    
    # Assicura che esista il record metadati per questa canzone
    cursor.execute('''
    INSERT OR IGNORE INTO canzoni_metadati (artista_pulito, titolo_pulito)
    VALUES (?, ?)
    ''', (artist_clean, title_clean))
    
    conn.commit()
    conn.close()

def get_monthly_unique_songs(year_month, id_radio=None):
    """
    Ritorna la lista delle canzoni uniche trasmesse in un dato mese (formato YYYY-MM)
    con i rispettivi metadati.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = '''
    SELECT DISTINCT 
        p.artista_pulito, 
        p.titolo_pulito,
        m.id as metadati_id,
        m.codice_siae,
        m.codice_iswc,
        m.codice_isrc,
        m.compositore,
        m.autore,
        m.casa_discografica,
        m.anno_pubblicazione
    FROM passaggi p
    LEFT JOIN canzoni_metadati m ON p.artista_pulito = m.artista_pulito AND p.titolo_pulito = m.titolo_pulito
    WHERE p.data LIKE ?
    '''
    params = [f"{year_month}%"]
    
    if id_radio:
        query += " AND p.id_radio = ?"
        params.append(id_radio)
        
    query += " ORDER BY p.artista_pulito, p.titolo_pulito"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_metadata(artist_clean, title_clean, siae, iswc, isrc, compositore, autore, label, year):
    """
    Aggiorna o inserisce centralmente i codici di una canzone.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO canzoni_metadati (artista_pulito, titolo_pulito, codice_siae, codice_iswc, codice_isrc, compositore, autore, casa_discografica, anno_pubblicazione)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(artista_pulito, titolo_pulito) DO UPDATE SET
        codice_siae = excluded.codice_siae,
        codice_iswc = excluded.codice_iswc,
        codice_isrc = excluded.codice_isrc,
        compositore = excluded.compositore,
        autore = excluded.autore,
        casa_discografica = excluded.casa_discografica,
        anno_pubblicazione = excluded.anno_pubblicazione
    ''', (artist_clean, title_clean, siae, iswc, isrc, compositore, autore, label, year))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
