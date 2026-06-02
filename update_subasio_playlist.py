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

# Configurazione Radio Subasio
JSON_DB = 'radio_subasio_history.json'
CACHE_YEARS = 'song_years_cache.json'
EXCEL_OUT = 'classifica_radio_subasio_STORICO.xlsx'
URL_BASE = "https://onlineradiobox.com/it/subasio/playlist/"

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
        # Altrimenti cerca nella cache scaricata da Wikipedia/Google
        year = cache.get(s, "N/A")
        cleaned = s
    
    cleaned = re.sub(r'^SRS\s+', '', cleaned).strip()
    return cleaned, year

def scrape_day(offset=0):
    url = URL_BASE if offset == 0 else f"{URL_BASE}{offset}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, 'html.parser')
        target_date = datetime.now() - timedelta(days=offset)
        date_str = target_date.strftime("%d.%m")
        day_el = soup.select_one('.menuitem_selected, .menuitem_active')
        if day_el:
            text = day_el.get_text(strip=True)
            match = re.search(r'(\d{2}\.\d{2})', text)
            if match: date_str = match.group(1)
        rows = soup.select('table.tablelist-schedule tr')
        data = []
        for row in rows:
            time_el = row.select_one('.time--schedule')
            song_el = row.select_one('.track_history_item a')
            if time_el and song_el:
                data.append({"date": date_str, "time": time_el.get_text(strip=True), "song": song_el.get_text(strip=True)})
        return data
    except Exception as e:
        print(f"Errore scraping: {e}")
        return []

def main():
    # 1. Carica dati
    if os.path.exists(JSON_DB):
        with open(JSON_DB, 'r', encoding='utf-8') as f: history = json.load(f)
    else: history = []
    
    cache = load_years_cache()
    seen = {f"{item['song']}|{item['date']}|{item['time']}" for item in history}
    initial_count = len(history)

    def is_near_duplicate(item, history, minutes=5):
        """True se lo stesso brano è già presente nello stesso giorno entro N minuti."""
        try:
            ih, im = map(int, item['time'].split(':'))
        except:
            return False
        for h in reversed(history[-50:]):  # controlla solo gli ultimi 50 per velocità
            if h['song'] == item['song'] and h['date'] == item['date']:
                try:
                    hh, hm = map(int, h['time'].split(':'))
                    if abs((ih*60+im) - (hh*60+hm)) <= minutes:
                        return True
                except:
                    pass
        return False

    # 2. Aggiorna passaggi
    print("Aggiornamento passaggi Radio Subasio...")
    # Recuperiamo sempre gli ultimi 7 giorni per coprire eventuali periodi di inattività
    for i in range(7):
        for item in scrape_day(i):
            uid = f"{item['song']}|{item['date']}|{item['time']}"
            if uid not in seen and not is_near_duplicate(item, history):
                history.append(item)
                seen.add(uid)

    added_count = len(history) - initial_count
    print(f"Aggiunti {added_count} nuovi passaggi Subasio.")

    with open(JSON_DB, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

    # 3. Elaborazione Excel
    song_stats = defaultdict(lambda: {"year": "N/A", "total": 0, "days": defaultdict(list)})
    all_dates = set()

    for item in history:
        name, year = parse_song(item['song'], cache)
        date = item['date']
        # Fix: aggiorna l'anno solo se non è già stato trovato (evita sovrascrittura con N/A)
        if song_stats[name]["year"] == "N/A" and year != "N/A":
            song_stats[name]["year"] = year
        song_stats[name]["total"] += 1
        song_stats[name]["days"][date].append(item['time'])
        all_dates.add(date)

    sorted_dates = sorted(list(all_dates), key=lambda x: datetime.strptime(x, "%d.%m"), reverse=True)
    sorted_ranking = sorted(song_stats.items(), key=lambda x: x[1]['total'], reverse=True)

    workbook = xlsxwriter.Workbook(EXCEL_OUT)
    ws = workbook.add_worksheet('Classifica Subasio')
    header_fmt = workbook.add_format({'bold': True, 'bg_color': '#CFE2F3', 'border': 1, 'align': 'center'})
    date_fmt = workbook.add_format({'text_wrap': True, 'valign': 'top', 'font_size': 9, 'border': 1})
    center_fmt = workbook.add_format({'align': 'center', 'valign': 'top', 'border': 1})
    song_fmt = workbook.add_format({'valign': 'top', 'border': 1})

    headers = ['Posizione', 'Canzone', 'Anno', 'Totale']
    for col, h in enumerate(headers): ws.write(0, col, h, header_fmt)
    for i, date in enumerate(sorted_dates): ws.write(0, len(headers) + i, date, header_fmt)

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
    print(f"Excel aggiornato con anni cercati: {EXCEL_OUT}")

if __name__ == "__main__":
    main()
