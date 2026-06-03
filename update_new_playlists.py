#!/usr/bin/env python3
import json
import os
import re
import sys
import requests
from bs4 import BeautifulSoup
import xlsxwriter
from collections import defaultdict
from datetime import datetime, timedelta

sys.stdout.reconfigure(line_buffering=True)

# Configurazione delle tre nuove radio
RADIOS = {
    'italia': {
        'json_db': 'radio_italia_history.json',
        'excel_out': 'classifica_radio_italia_STORICO.xlsx',
        'url_base': 'https://myradioonline.it/radio-italia/playlist',
        'label': 'Radio Italia',
        'source': 'myradioonline'
    },
    'rds': {
        'json_db': 'radio_rds_history.json',
        'excel_out': 'classifica_radio_rds_STORICO.xlsx',
        'url_base': 'https://onlineradiobox.com/it/rds/playlist/',
        'label': 'RDS',
        'source': 'onlineradiobox'
    },
    'rtl1025': {
        'json_db': 'radio_rtl1025_history.json',
        'excel_out': 'classifica_radio_rtl1025_STORICO.xlsx',
        'url_base': 'https://myradioonline.it/rtl-102-5/playlist',
        'label': 'RTL 102.5',
        'source': 'myradioonline'
    },
    'birikina': {
        'json_db': 'radio_birikina_history.json',
        'excel_out': 'classifica_radio_birikina_STORICO.xlsx',
        'url_base': 'https://onlineradiobox.com/it/birikina/playlist/',
        'label': 'Radio Birikina',
        'source': 'onlineradiobox'
    },
    'bruno': {
        'json_db': 'radio_bruno_history.json',
        'excel_out': 'classifica_radio_bruno_STORICO.xlsx',
        'url_base': 'https://onlineradiobox.com/it/bruno/playlist/',
        'label': 'Radio Bruno',
        'source': 'onlineradiobox'
    },
    'kisskiss': {
        'json_db': 'radio_kisskiss_history.json',
        'excel_out': 'classifica_radio_kisskiss_STORICO.xlsx',
        'url_base': 'https://onlineradiobox.com/it/kisskiss/playlist/',
        'label': 'Radio Kiss Kiss',
        'source': 'onlineradiobox'
    },
    'm2o': {
        'json_db': 'radio_m2o_history.json',
        'excel_out': 'classifica_radio_m2o_STORICO.xlsx',
        'url_base': 'https://myradioonline.it/m2o/playlist',
        'label': 'Radio m2o',
        'source': 'myradioonline'
    },
    'propostaaosta': {
        'json_db': 'radio_propostaaosta_history.json',
        'excel_out': 'classifica_radio_propostaaosta_STORICO.xlsx',
        'url_base': 'https://onlineradiobox.com/it/propostaaosta/playlist/',
        'label': 'Proposta Aosta',
        'source': 'onlineradiobox'
    },
    'capital': {
        'json_db': 'radio_capital_history.json',
        'excel_out': 'classifica_radio_capital_STORICO.xlsx',
        'url_base': 'https://myradioonline.it/radio-capital/playlist',
        'label': 'Radio Capital',
        'source': 'myradioonline'
    }
}

CACHE_YEARS = 'song_years_cache.json'

def load_years_cache():
    if os.path.exists(CACHE_YEARS):
        with open(CACHE_YEARS, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def parse_song(s, cache):
    # Prova a estrarre l'anno dal titolo (se presente)
    match = re.search(r'\((\d{4})\)', s)
    if match:
        year = match.group(1)
        cleaned = re.sub(r'\s*\(\d{4}\)\s*$', '', s)
    else:
        # Altrimenti cerca nella cache
        year = cache.get(s, "N/A")
        cleaned = s
    
    cleaned = re.sub(r'^SRS\s+', '', cleaned).strip()
    return cleaned, year

def scrape_day_onlineradiobox(url_base, label, offset=0):
    url = url_base if offset == 0 else f"{url_base}{offset}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, 'html.parser')
        
        target_date = datetime.now() - timedelta(days=offset)
        expected_date_str = target_date.strftime("%d.%m")
        date_str = expected_date_str
        
        day_el = soup.select_one('.menuitem_selected, .menuitem_active')
        if day_el:
            text = day_el.get_text(strip=True)
            match = re.search(r'(\d{2}\.\d{2})', text)
            if match:
                date_str = match.group(1)
                
        if date_str != expected_date_str:
            return []
            
        rows = soup.select('table.tablelist-schedule tr')
        data = []
        for row in rows:
            time_el = row.select_one('.time--schedule')
            song_el = row.select_one('.track_history_item a')
            if time_el and song_el:
                data.append({
                    "date": date_str,
                    "time": time_el.get_text(strip=True),
                    "song": song_el.get_text(strip=True)
                })
        return data
    except Exception as e:
        print(f"  Errore scraping {label} offset {offset}: {e}")
        return []

def scrape_day_myradioonline(url_base, label, offset=0):
    target_date = datetime.now() - timedelta(days=offset)
    date_str_payload = target_date.strftime("%d-%m-%Y")
    expected_date_str = target_date.strftime("%d.%m")
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    data = {
        'from': date_str_payload,
        'to': date_str_payload
    }
    
    try:
        r = requests.post(url_base, data=data, headers=headers, timeout=15)
        if r.status_code != 200:
            print(f"  [{label}] POST err code {r.status_code}")
            return []
            
        soup = BeautifulSoup(r.text, 'html.parser')
        rows = soup.select('.js-songListC .yt-row')
        
        extracted_data = []
        for row in rows:
            artist_el = row.select_one('[itemprop="byArtist"]')
            title_el = row.select_one('[itemprop="name"]')
            time_el = row.select_one('.txt2.mcolumn')
            
            if artist_el and title_el and time_el:
                artist = artist_el.get_text(strip=True)
                title = title_el.get_text(strip=True)
                time_text = time_el.get_text(strip=True)
                
                # Se il titolo è vuoto, proviamo a dividere il campo artist (che per m2o contiene la stringa unita)
                if not title and artist:
                    words = artist.split()
                    artist_start_idx = len(words)
                    
                    def is_uppercase_word(w):
                        clean_w = re.sub(r'[^a-zA-Z0-9]', '', w)
                        if not clean_w:
                            return True
                        return clean_w.isupper()
                        
                    for i in range(len(words) - 1, -1, -1):
                        if is_uppercase_word(words[i]):
                            artist_start_idx = i
                        else:
                            break
                            
                    if 0 < artist_start_idx < len(words):
                        title = " ".join(words[:artist_start_idx]).strip()
                        artist = " ".join(words[artist_start_idx:]).strip()
                
                # Estrai ora e data
                m = re.search(r'(\d{2}\.\d{2})\s+(\d{2}:\d{2})', time_text)
                if m:
                    date_val = m.group(1)
                    time_val = m.group(2)
                    
                    if date_val == expected_date_str:
                        if title:
                            song_name = f"{artist.upper()} - {title.upper()}"
                        else:
                            song_name = artist.upper()
                        extracted_data.append({
                            "date": date_val,
                            "time": time_val,
                            "song": song_name
                        })
        return extracted_data
    except Exception as e:
        print(f"  Errore scraping {label} (MyRadioOnline) offset {offset}: {e}")
        return []

def update_radio(key, config, cache):
    json_db = config['json_db']
    excel_out = config['excel_out']
    url_base = config['url_base']
    label = config['label']
    source = config['source']
    
    print(f"\n--- Aggiornamento passaggi {label} ({source}) ---")
    
    # 1. Carica storico esistente
    if os.path.exists(json_db):
        with open(json_db, 'r', encoding='utf-8') as f:
            history = json.load(f)
    else:
        history = []
        
    seen = {f"{item['song']}|{item['date']}|{item['time']}" for item in history}
    initial_count = len(history)

    def is_near_duplicate(item, history, minutes=5):
        try:
            ih, im = map(int, item['time'].split(':'))
        except:
            return False
        for h in reversed(history[-50:]):
            if h['song'] == item['song'] and h['date'] == item['date']:
                try:
                    hh, hm = map(int, h['time'].split(':'))
                    if abs((ih*60+im) - (hh*60+hm)) <= minutes:
                        return True
                except:
                    pass
        return False

    # 2. Scraping ultimi 7 giorni
    for i in range(7):
        if source == 'myradioonline':
            day_data = scrape_day_myradioonline(url_base, label, i)
        else:
            day_data = scrape_day_onlineradiobox(url_base, label, i)
            
        for item in day_data:
            uid = f"{item['song']}|{item['date']}|{item['time']}"
            if uid not in seen and not is_near_duplicate(item, history):
                history.append(item)
                seen.add(uid)

    added_count = len(history) - initial_count
    print(f"  Aggiunti {added_count} nuovi passaggi per {label}.")

    with open(json_db, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

    # 3. Elaborazione Excel storico
    song_stats = defaultdict(lambda: {"year": "N/A", "total": 0, "days": defaultdict(list)})
    all_dates = set()

    for item in history:
        name, year = parse_song(item['song'], cache)
        date = item['date']
        if song_stats[name]["year"] == "N/A" and year != "N/A":
            song_stats[name]["year"] = year
        song_stats[name]["total"] += 1
        song_stats[name]["days"][date].append(item['time'])
        all_dates.add(date)

    sorted_dates = sorted(list(all_dates), key=lambda x: datetime.strptime(x, "%d.%m"), reverse=True)
    sorted_ranking = sorted(song_stats.items(), key=lambda x: x[1]['total'], reverse=True)

    workbook = xlsxwriter.Workbook(excel_out)
    ws = workbook.add_worksheet(f'Classifica {label}')
    header_fmt = workbook.add_format({'bold': True, 'bg_color': '#D9EAD3', 'border': 1, 'align': 'center'})
    date_fmt = workbook.add_format({'text_wrap': True, 'valign': 'top', 'font_size': 9, 'border': 1})
    center_fmt = workbook.add_format({'align': 'center', 'valign': 'top', 'border': 1})
    song_fmt = workbook.add_format({'valign': 'top', 'border': 1})

    headers = ['Posizione', 'Canzone', 'Anno', 'Totale']
    for col, h in enumerate(headers):
        ws.write(0, col, h, header_fmt)
    for i, date in enumerate(sorted_dates):
        ws.write(0, len(headers) + i, date, header_fmt)

    for row_idx, (name, info) in enumerate(sorted_ranking, 1):
        ws.write(row_idx, 0, row_idx, center_fmt)
        ws.write(row_idx, 1, name, song_fmt)
        ws.write(row_idx, 2, info['year'], center_fmt)
        ws.write(row_idx, 3, info['total'], center_fmt)
        for col_offset, date in enumerate(sorted_dates):
            ws.write(row_idx, len(headers) + col_offset, ", ".join(info["days"].get(date, [])), date_fmt)

    ws.set_column(1, 1, 45)
    ws.set_column(4, 4 + len(sorted_dates), 20)
    ws.freeze_panes(1, 4)
    workbook.close()
    print(f"  Excel {label} salvato: {excel_out}")

def main():
    cache = load_years_cache()
    for key, config in RADIOS.items():
        update_radio(key, config, cache)
    print("\nFine aggiornamento nuove radio!")

if __name__ == "__main__":
    main()
