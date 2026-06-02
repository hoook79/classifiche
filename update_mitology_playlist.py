import json
import os
import re
import requests
from bs4 import BeautifulSoup
import xlsxwriter
from collections import defaultdict
from datetime import datetime, timedelta
import sys
sys.stdout.reconfigure(line_buffering=True)

JSON_DB   = 'radio_mitology_history.json'
EXCEL_OUT = 'classifica_radio_mitology_STORICO.xlsx'
URL_BASE  = "https://onlineradiobox.com/it/mitology7080/playlist/"

def parse_song(s):
    match = re.search(r'\((\d{4})\)', s)
    year = match.group(1) if match else "N/A"
    cleaned = re.sub(r'\s*\(\d{4}\)\s*$', '', s).strip()
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

        if date_str != expected_date_str:
            print(f"  Offset {offset}: data pagina ({date_str}) ≠ attesa ({expected_date_str}), skip.", flush=True)
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
        print(f"Errore scraping Mitology offset {offset}: {e}", flush=True)
        return []

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    json_path  = os.path.join(base_dir, JSON_DB)
    excel_path = os.path.join(base_dir, EXCEL_OUT)

    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            history = json.load(f)
    else:
        history = []

    seen = {f"{item['song']}|{item['date']}|{item['time']}" for item in history}

    print("Aggiornamento dati Radio Mitology...", flush=True)
    added_count = 0
    for i in range(7):
        day_data = scrape_day(i)
        for item in day_data:
            uid = f"{item['song']}|{item['date']}|{item['time']}"
            if uid not in seen:
                history.append(item)
                seen.add(uid)
                added_count += 1

    print(f"Aggiunti {added_count} nuovi passaggi Mitology.", flush=True)

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

    song_stats = defaultdict(lambda: {"year": "N/A", "total": 0, "days": defaultdict(list)})
    all_dates = set()

    for item in history:
        name, year = parse_song(item['song'])
        date = item['date']
        if song_stats[name]["year"] == "N/A" and year != "N/A":
            song_stats[name]["year"] = year
        song_stats[name]["total"] += 1
        song_stats[name]["days"][date].append(item['time'])
        all_dates.add(date)

    def sort_date_key(d):
        try:
            parts = d.split('.')
            day, month = int(parts[0]), int(parts[1])
            year = 2025 if month >= 10 else 2026
            return datetime(year, month, day)
        except:
            return datetime(2026, 1, 1)

    sorted_dates   = sorted(all_dates, key=sort_date_key, reverse=True)
    sorted_ranking = sorted(song_stats.items(), key=lambda x: x[1]['total'], reverse=True)

    workbook = xlsxwriter.Workbook(excel_path)
    ws = workbook.add_worksheet('Classifica Mitology')

    header_fmt = workbook.add_format({'bold': True, 'bg_color': '#FCE4D6', 'border': 1, 'align': 'center'})
    date_fmt   = workbook.add_format({'text_wrap': True, 'valign': 'top', 'font_size': 9, 'border': 1})
    center_fmt = workbook.add_format({'align': 'center', 'valign': 'top', 'border': 1})
    song_fmt   = workbook.add_format({'valign': 'top', 'border': 1})

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
    print(f"Excel Mitology aggiornato: {EXCEL_OUT}", flush=True)

if __name__ == "__main__":
    main()
