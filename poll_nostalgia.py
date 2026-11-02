#!/usr/bin/env python3
"""
Radio Nostalgia Toscana: onlineradiobox non pubblica più la playlist (da ottobre 2026).
Questo script legge gli ultimi brani dal player del sito ufficiale e li aggiunge a
radio_nostalgia_history.json. L'API restituisce solo ~10 elementi (20-30 minuti),
quindi va eseguito ogni 10 minuti (Utilità di pianificazione di Windows).
"""
import os
import json
import requests
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_DB = os.path.join(BASE_DIR, 'radio_nostalgia_history.json')
API_URL = "https://www.radionostalgia.fm/player/api.php?action=metadata"
LOG_FILE = os.path.join(BASE_DIR, 'script_outputs', 'poll_nostalgia.log')


def log(msg):
    line = f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')} {msg}"
    print(line, flush=True)
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except OSError:
        pass


def is_jingle(artist, title):
    return artist.strip().upper() == '70 80 E 90' or title.strip().upper() == 'RADIO NOSTALGIA'


def fetch_items():
    r = requests.get(API_URL, params={'_t': int(datetime.now().timestamp() * 1000)},
                     headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
    r.raise_for_status()
    data = r.json()
    items = []
    for h in data.get('history', []):
        artist = (h.get('artist') or '').strip()
        title = (h.get('title') or '').strip()
        ts = h.get('time')
        if not artist or not title or not ts or is_jingle(artist, title):
            continue
        dt = datetime.fromtimestamp(ts / 1000)
        items.append({
            "date": dt.strftime("%d.%m"),
            "time": dt.strftime("%H:%M"),
            "song": f"{artist} - {title}"
        })
    return items


def main():
    try:
        items = fetch_items()
    except Exception as e:
        log(f"[ERRORE] Lettura API Radio Nostalgia: {e}")
        return

    try:
        with open(JSON_DB, 'r', encoding='utf-8') as f:
            history = json.load(f)
    except FileNotFoundError:
        history = []
    except Exception as e:
        # Non sovrascrivere uno storico che non si riesce a leggere
        log(f"[ERRORE] Impossibile leggere {JSON_DB}: {e}")
        return

    seen = {f"{x['song']}|{x['date']}|{x['time']}" for x in history}
    added = 0
    for item in sorted(items, key=lambda x: (x['date'][3:], x['date'][:2], x['time'])):
        uid = f"{item['song']}|{item['date']}|{item['time']}"
        if uid not in seen:
            history.append(item)
            seen.add(uid)
            added += 1

    if added:
        tmp_file = f"{JSON_DB}.tmp"
        with open(tmp_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        os.replace(tmp_file, JSON_DB)
    log(f"Radio Nostalgia: {added} nuovi passaggi aggiunti ({len(items)} letti dall'API).")


if __name__ == "__main__":
    main()
