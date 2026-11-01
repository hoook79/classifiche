#!/usr/bin/env python3
"""
Sincronizza i passaggi dai file radio_*_history.json nel database radio_reports.db
(usato dalla dashboard). Importa solo i giorni dall'ultima data presente nel DB
per ciascuna radio in poi, saltando i passaggi già presenti.
"""
import os
import json
import datetime
from data_cleaner import clean_song
from db_manager import init_db, get_db_connection

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RADIOS = {
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

# I JSON hanno date senza anno (DD.MM): consideriamo solo gli ultimi N giorni,
# così l'anno si ricava senza ambiguità (anno corrente, o precedente se la data sarebbe nel futuro)
MAX_DAYS_BACK = 180


def parse_date(date_raw, today):
    try:
        day, month = date_raw.split('.')[:2]
        d = datetime.date(today.year, int(month), int(day))
    except (ValueError, IndexError):
        return None
    if d > today:
        try:
            d = d.replace(year=today.year - 1)
        except ValueError:  # 29 febbraio
            return None
    return d


def parse_time(time_raw):
    parts = time_raw.split(':')
    if len(parts) == 2:
        parts.append('00')
    if len(parts) != 3 or not all(p.strip().isdigit() for p in parts):
        return None  # es. "In diretta"
    return ':'.join(p.strip().zfill(2) for p in parts)


def sync():
    init_db()
    today = datetime.date.today()
    oldest_allowed = today - datetime.timedelta(days=MAX_DAYS_BACK)

    conn = get_db_connection()
    cursor = conn.cursor()
    total_inserted = 0

    for filename, radio_id in RADIOS.items():
        path = os.path.join(BASE_DIR, filename)
        if not os.path.exists(path):
            print(f"[{radio_id}] File {filename} non trovato, salto.")
            continue

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"[{radio_id}] Errore lettura {filename}: {e}")
            continue

        row = cursor.execute('SELECT MAX(data) FROM passaggi WHERE id_radio = ?', (radio_id,)).fetchone()
        last_date = datetime.date.fromisoformat(row[0]) if row[0] else oldest_allowed
        start_date = max(last_date, oldest_allowed)
        start_iso = start_date.isoformat()

        # Passaggi già presenti dal giorno di partenza in poi (per evitare duplicati)
        existing = set(cursor.execute(
            'SELECT data, ora, artista, titolo FROM passaggi WHERE id_radio = ? AND data >= ?',
            (radio_id, start_iso)
        ).fetchall())
        existing = {tuple(r) for r in existing}

        passages = []
        metadata = set()
        for item in data:
            date_raw = item.get('date', '')
            time_raw = item.get('time', '')
            song_raw = item.get('song', '')
            if not song_raw or not date_raw or not time_raw:
                continue

            d = parse_date(date_raw, today)
            time_iso = parse_time(time_raw)
            if d is None or time_iso is None or d < start_date:
                continue
            date_iso = d.isoformat()

            if ' - ' in song_raw:
                artist, title = song_raw.split(' - ', 1)
            else:
                artist, title = "Unknown", song_raw

            key = (date_iso, time_iso, artist, title)
            if key in existing:
                continue
            existing.add(key)

            artist_clean, title_clean = clean_song(artist, title)
            passages.append((radio_id, date_iso, time_iso, artist, title, artist_clean, title_clean, 'IMPORT_LOG'))
            metadata.add((artist_clean, title_clean))

        if passages:
            cursor.executemany('''
            INSERT INTO passaggi (id_radio, data, ora, artista, titolo, artista_pulito, titolo_pulito, sorgente)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', passages)
            cursor.executemany('''
            INSERT OR IGNORE INTO canzoni_metadati (artista_pulito, titolo_pulito)
            VALUES (?, ?)
            ''', list(metadata))
            conn.commit()

        new_last = max((p[1] for p in passages), default=start_iso)
        print(f"[{radio_id}] Importati {len(passages)} nuovi passaggi (dal {start_iso}, ultimo giorno ora: {new_last}).")
        total_inserted += len(passages)

    conn.close()
    print(f"\nSincronizzazione database completata: {total_inserted} passaggi importati.")


if __name__ == "__main__":
    sync()
