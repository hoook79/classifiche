import json
import os
import re
import requests
from bs4 import BeautifulSoup
import xlsxwriter
from collections import defaultdict
from datetime import datetime, timedelta

# Configurazione Radio Divina
JSON_DB = 'radio_divina_history.json'
EXCEL_OUT = 'classifica_radio_divina_STORICO.xlsx'
URL_BASE = "https://onlineradiobox.com/it/divina/playlist/"

def parse_song(s):
    match = re.search(r'\((\d{4})\)', s)
    year = match.group(1) if match else "N/A"
    cleaned = re.sub(r'\s*\(\d{4}\)\s*$', '', s)
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
        expected_date_str = target_date.strftime("%d.%m")
        date_str = expected_date_str

        day_el = soup.select_one('.menuitem_selected, .menuitem_active')
        if day_el:
            text = day_el.get_text(strip=True)
            match = re.search(r'(\d{2}\.\d{2})', text)
            if match:
                date_str = match.group(1)

        # Se la data rilevata non corrisponde a quella attesa, la pagina
        # probabilmente non è cambiata ancora (es. il sito riusa la pagina
        # del giorno precedente). In questo caso saltiamo per evitare duplicati.
        if date_str != expected_date_str:
            print(f"  Offset {offset}: data pagina ({date_str}) ≠ attesa ({expected_date_str}), skip.")
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
        print(f"Errore scraping Divina offset {offset}: {e}")
        return []

def main():
    if os.path.exists(JSON_DB):
        with open(JSON_DB, 'r', encoding='utf-8') as f:
            history = json.load(f)
    else:
        history = []

    seen = {f"{item['song']}|{item['date']}|{item['time']}" for item in history}

    print(f"Aggiornamento dati Radio Divina...")
    added_count = 0
    # Recuperiamo sempre gli ultimi 7 giorni per coprire eventuali periodi di inattività
    for i in range(7):
        day_data = scrape_day(i)
        for item in day_data:
            uid = f"{item['song']}|{item['date']}|{item['time']}"
            if uid not in seen:
                history.append(item)
                seen.add(uid)
                added_count += 1
    
    print(f"Aggiunti {added_count} nuovi passaggi Divina.")

    with open(JSON_DB, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

    song_stats = defaultdict(lambda: {"year": "", "total": 0, "days": defaultdict(list)})
    all_dates = set()

    for item in history:
        name, year = parse_song(item['song'])
        date = item['date']
        song_stats[name]["year"] = year
        song_stats[name]["total"] += 1
        song_stats[name]["days"][date].append(item['time'])
        all_dates.add(date)

    sorted_dates = sorted(list(all_dates), key=lambda x: datetime.strptime(x, "%d.%m"), reverse=True)
    sorted_ranking = sorted(song_stats.items(), key=lambda x: x[1]['total'], reverse=True)

    workbook = xlsxwriter.Workbook(EXCEL_OUT)
    ws = workbook.add_worksheet('Classifica Divina')
    
    header_fmt = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1, 'align': 'center'})
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
            times = info["days"].get(date, [])
            ws.write(row_idx, len(headers) + col_offset, ", ".join(times), date_fmt)

    ws.set_column(0, 0, 10)
    ws.set_column(1, 1, 45)
    ws.set_column(2, 2, 8)
    ws.set_column(3, 3, 10)
    ws.set_column(4, 4 + len(sorted_dates), 20)
    
    ws.freeze_panes(1, 4)
    workbook.close()
    print(f"Excel Divina aggiornato con colonne giornaliere: {EXCEL_OUT}")

if __name__ == "__main__":
    main()
