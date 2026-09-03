#!/usr/bin/env python3
import os
import json
import sqlite3
from data_cleaner import clean_song
from db_manager import init_db, get_db_connection

def migrate_caches():
    print("Migrazione dei cache degli anni...")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Carica song_years_cache.json
    years_cache_file = 'song_years_cache.json'
    years_data = {}
    if os.path.exists(years_cache_file):
        with open(years_cache_file, 'r', encoding='utf-8') as f:
            try:
                years_data = json.load(f)
            except Exception as e:
                print(f"Errore caricamento cache anni: {e}")
                
    # 2. Carica manual_years_override.json
    overrides_file = 'manual_years_override.json'
    overrides_data = {}
    if os.path.exists(overrides_file):
        with open(overrides_file, 'r', encoding='utf-8') as f:
            try:
                overrides_data = json.load(f)
            except Exception as e:
                print(f"Errore caricamento overrides anni: {e}")
                
    # Unisci i dati
    merged_years = {}
    for k, v in years_data.items():
        if v and v != 'N/A':
            merged_years[k] = v
    for k, v in overrides_data.items():
        if v and v != 'N/A':
            merged_years[k] = v
            
    print(f"Trovate {len(merged_years)} canzoni con anno di pubblicazione nei cache.")
    
    # Inserisci in blocco
    inserted = 0
    batch = []
    for song_str, year in merged_years.items():
        if ' - ' in song_str:
            artist, title = song_str.split(' - ', 1)
        else:
            artist, title = "Unknown", song_str
            
        artist_clean, title_clean = clean_song(artist, title)
        batch.append((artist_clean, title_clean, year))
        
        if len(batch) >= 1000:
            cursor.executemany('''
            INSERT OR IGNORE INTO canzoni_metadati (artista_pulito, titolo_pulito, anno_pubblicazione)
            VALUES (?, ?, ?)
            ''', batch)
            # Fai anche update se l'anno è nuovo
            cursor.executemany('''
            UPDATE canzoni_metadati SET anno_pubblicazione = ? 
            WHERE artista_pulito = ? AND titolo_pulito = ? AND (anno_pubblicazione IS NULL OR anno_pubblicazione = '')
            ''', [(y, a, t) for a, t, y in batch])
            inserted += len(batch)
            batch = []
            
    if batch:
        cursor.executemany('''
        INSERT OR IGNORE INTO canzoni_metadati (artista_pulito, titolo_pulito, anno_pubblicazione)
        VALUES (?, ?, ?)
        ''', batch)
        cursor.executemany('''
        UPDATE canzoni_metadati SET anno_pubblicazione = ? 
        WHERE artista_pulito = ? AND titolo_pulito = ? AND (anno_pubblicazione IS NULL OR anno_pubblicazione = '')
        ''', [(y, a, t) for a, t, y in batch])
        inserted += len(batch)
        
    conn.commit()
    conn.close()
    print(f"Completata migrazione cache anni. Inserite/aggiornate {inserted} canzoni.")

def migrate_history_files():
    print("Migrazione dei file storici di passaggi...")
    
    radios = {
        'radio_subasio_history.json': 'subasio',
        'radio_divina_history.json': 'divina',
        'radio_mitology_history.json': 'mitology',
        'radio_nostalgia_history.json': 'nostalgia',
        'radio_toscana_history.json': 'toscana',
        'radio_italia_history.json': 'italia',
        'radio_rds_history.json': 'rds',
        'radio_rtl1025_history.json': 'rtl1025',
        'radio_birikina_history.json': 'birikina',
        'radio_bruno_history.json': 'bruno',
        'radio_kisskiss_history.json': 'kisskiss',
        'radio_m2o_history.json': 'm2o',
        'radio_propostaaosta_history.json': 'propostaaosta',
        'radio_capital_history.json': 'capital'
    }
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    total_inserted = 0
    
    for filename, radio_id in radios.items():
        if not os.path.exists(filename):
            print(f"File {filename} non trovato, salto.")
            continue
            
        print(f"Elaborazione {filename}...")
        with open(filename, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except Exception as e:
                print(f"Errore durante il parsing di {filename}: {e}")
                continue
                
        passages_batch = []
        metadata_batch = set()
        
        for item in data:
            date_raw = item.get('date', '')
            time_raw = item.get('time', '')
            song_raw = item.get('song', '')
            
            if not song_raw or not date_raw or not time_raw:
                continue
                
            # Parsa data DD.MM -> YYYY-MM-DD
            try:
                parts = date_raw.split('.')
                day = parts[0].zfill(2)
                month = parts[1].zfill(2)
                year = "2025" if int(month) >= 10 else "2026"
                date_iso = f"{year}-{month}-{day}"
            except:
                continue
                
            # Parsa ora HH:MM -> HH:MM:SS
            time_parts = time_raw.split(':')
            if len(time_parts) == 2:
                time_iso = f"{time_parts[0].zfill(2)}:{time_parts[1].zfill(2)}:00"
            elif len(time_parts) == 3:
                time_iso = f"{time_parts[0].zfill(2)}:{time_parts[1].zfill(2)}:{time_parts[2].zfill(2)}"
            else:
                continue
                
            if ' - ' in song_raw:
                artist, title = song_raw.split(' - ', 1)
            else:
                artist, title = "Unknown", song_raw
                
            artist_clean, title_clean = clean_song(artist, title)
            
            passages_batch.append((radio_id, date_iso, time_iso, artist, title, artist_clean, title_clean, 'IMPORT_LOG'))
            metadata_batch.add((artist_clean, title_clean))
            
            if len(passages_batch) >= 2000:
                # Inserisci passaggi
                cursor.executemany('''
                INSERT INTO passaggi (id_radio, data, ora, artista, titolo, artista_pulito, titolo_pulito, sorgente)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', passages_batch)
                
                # Inserisci metadati ignorando duplicati
                cursor.executemany('''
                INSERT OR IGNORE INTO canzoni_metadati (artista_pulito, titolo_pulito)
                VALUES (?, ?)
                ''', list(metadata_batch))
                
                total_inserted += len(passages_batch)
                passages_batch = []
                metadata_batch = set()
                
        if passages_batch:
            cursor.executemany('''
            INSERT INTO passaggi (id_radio, data, ora, artista, titolo, artista_pulito, titolo_pulito, sorgente)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', passages_batch)
            
            cursor.executemany('''
            INSERT OR IGNORE INTO canzoni_metadati (artista_pulito, titolo_pulito)
            VALUES (?, ?)
            ''', list(metadata_batch))
            
            total_inserted += len(passages_batch)
            
        print(f"Inseriti {total_inserted} passaggi in totale finora.")
        
    conn.commit()
    conn.close()
    print("Migrazione dei file storici completata con successo.")

def main():
    # Inizializza DB (crea tabelle e indici)
    init_db()
    # Migra cache anni per non perdere dati storici
    migrate_caches()
    # Importa tutti i vecchi passaggi dai file JSON
    migrate_history_files()
    print("\nInizializzazione database ed importazione storico completate con successo!")

if __name__ == "__main__":
    main()
