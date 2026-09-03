#!/usr/bin/env python3
import sys
import os
import re
import time
import requests
import urllib.parse
from bs4 import BeautifulSoup
from datetime import datetime, date, timedelta
from db_manager import insert_passage

SLUGS = {
    'subasio': 'subasio',
    'divina': 'divina',
    'mitology': 'mitology7080',
    'nostalgia': 'nostalgiatoscana875',
    'toscana': 'toscana',
    'rds': 'rds',
    'birikina': 'birikina',
    'bruno': 'bruno',
    'kisskiss': 'kisskiss',
    'propostaaosta': 'propostaaosta',
    'capital': 'capital',
    'italia': 'radioitalia',
    'rtl1025': 'rtl1025',
    'm2o': 'm2o'
}

def get_wayback_snapshot(slug, target_date):
    """
    Interroga archive.org per trovare lo snapshot di Online Radio Box più pertinente.
    Ritorna l'URL dello snapshot se trovato, altrimenti None.
    """
    url_1 = f"https://onlineradiobox.com/it/{slug}/playlist/"
    ts_1 = target_date.strftime("%Y%m%d235959")
    
    print(f"[ARCHIVE.ORG] Ricerca snapshot per {url_1} vicino a {ts_1}...")
    api_url = f"https://archive.org/wayback/available?url={urllib.parse.quote(url_1)}&timestamp={ts_1}"
    
    try:
        r = requests.get(api_url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            snapshot = data.get("archived_snapshots", {}).get("closest", {})
            if snapshot and snapshot.get("available"):
                snap_url = snapshot.get("url")
                snap_ts = snapshot.get("timestamp")
                # Se lo snapshot è entro un intervallo ragionevole della data target
                if snap_ts.startswith(target_date.strftime("%Y%m")):
                    print(f"[ARCHIVE.ORG] Snapshot trovato: {snap_url} (Data: {snap_ts})")
                    return snap_url
                    
        # Fallback 2: prova /playlist/1 il giorno dopo
        day_after = target_date + timedelta(days=1)
        url_2 = f"https://onlineradiobox.com/it/{slug}/playlist/1"
        ts_2 = day_after.strftime("%Y%m%d120000")
        
        print(f"[ARCHIVE.ORG] Ricerca snapshot fallback per {url_2} vicino a {ts_2}...")
        api_url_2 = f"https://archive.org/wayback/available?url={urllib.parse.quote(url_2)}&timestamp={ts_2}"
        
        r = requests.get(api_url_2, timeout=10)
        if r.status_code == 200:
            data = r.json()
            snapshot = data.get("archived_snapshots", {}).get("closest", {})
            if snapshot and snapshot.get("available"):
                snap_url = snapshot.get("url")
                snap_ts = snapshot.get("timestamp")
                if snap_ts.startswith(day_after.strftime("%Y%m")):
                    print(f"[ARCHIVE.ORG] Snapshot fallback trovato: {snap_url} (Data: {snap_ts})")
                    return snap_url
    except Exception as e:
        print(f"[ARCHIVE.ORG] Errore durante la ricerca di snapshot: {e}")
    return None

def scrape_retro(radio_id, target_date_str):
    """
    Scrape retroattivo da Online Radio Box.
    radio_id: ID interno (es: 'subasio')
    target_date_str: data in formato YYYY-MM-DD o DD-MM-YYYY
    """
    # Normalizza data in datetime.date
    try:
        if '-' in target_date_str:
            if len(target_date_str.split('-')[0]) == 4:
                target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
            else:
                target_date = datetime.strptime(target_date_str, "%d-%m-%Y").date()
        elif '/' in target_date_str:
            target_date = datetime.strptime(target_date_str, "%d/%m/%Y").date()
        elif '.' in target_date_str:
            target_date = datetime.strptime(target_date_str, "%d.%m.%Y").date()
        else:
            raise ValueError("Formato data non riconosciuto")
    except Exception as e:
        print(f"[ERRORE] Formato data '{target_date_str}' non valido. Usa YYYY-MM-DD.")
        return False, f"Formato data non valido: {str(e)}"

    slug = SLUGS.get(radio_id.lower())
    if not slug:
        # Se non è in mappa, prova a usarlo direttamente come slug
        slug = radio_id.lower()
        print(f"[INFO] Radio ID '{radio_id}' non presente in mappa standard. Provo a usarlo come slug ORB: '{slug}'")

    today = date.today()
    delta = today - target_date
    offset = delta.days

    if offset < 0:
        return False, "Non puoi recuperare dati futuri."
    
    use_wayback = False
    wayback_url = None
    
    if offset > 7:
        print(f"[INFO] L'offset è di {offset} giorni fa. Online Radio Box conserva solo gli ultimi 7 giorni. Ricerca su archive.org...")
        wayback_url = get_wayback_snapshot(slug, target_date)
        if wayback_url:
            url = wayback_url
            use_wayback = True
        else:
            print("[ARCHIVE.ORG] Nessuno snapshot trovato su archive.org per questa data. Provo comunque l'URL live...")
            url = f"https://onlineradiobox.com/it/{slug}/playlist/{offset}"
    else:
        # Costruisci l'URL live
        if offset == 0:
            url = f"https://onlineradiobox.com/it/{slug}/playlist/"
        else:
            url = f"https://onlineradiobox.com/it/{slug}/playlist/{offset}"

    print(f"Richiesta URL: {url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7'
    }

    # Delay per evitare ban IP
    time.sleep(2.0)

    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200:
            return False, f"Errore HTTP {r.status_code} da Online Radio Box."
            
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, 'html.parser')

        # Verifica la data della pagina se possibile
        # Cerca l'elemento del calendario selezionato
        page_date_str = ""
        day_el = soup.select_one('.menuitem_selected, .menuitem_active, .playlist-calendar .selected')
        if day_el:
            page_date_str = day_el.get_text(strip=True)
            print(f"Data rilevata sulla pagina ORB: '{page_date_str}' (richiesta: '{target_date.strftime('%d.%m')}')")

        rows = soup.select('table.tablelist-schedule tr')
        if not rows:
            return False, "Nessun passaggio trovato nella pagina. La data potrebbe essere troppo vecchia o lo slug non valido."

        count = 0
        inserted_count = 0
        date_iso = target_date.strftime("%Y-%m-%d")

        for row in rows:
            time_el = row.select_one('.time--schedule')
            song_el = row.select_one('.track_history_item a')
            if not song_el:
                song_el = row.select_one('.track_history_item')
                
            if time_el and song_el:
                time_val = time_el.get_text(strip=True)
                song_val = song_el.get_text(strip=True)
                
                # Pulisce i caratteri
                song_val = re.sub(r'\s+', ' ', song_val).strip()
                
                if not song_val or len(song_val) < 4:
                    continue
                
                # Filtra jingle o promo se contengono parole chiave radio o sono troppo corti
                # (Lasciamo che db_manager faccia la pulizia interna del titolo/artista)
                if ' - ' in song_val:
                    artist, title = song_val.split(' - ', 1)
                else:
                    artist, title = "Unknown", song_val
                    
                # Formatta ora come HH:MM:SS
                if len(time_val.split(':')) == 2:
                    time_val = f"{time_val}:00"
                
                insert_passage(
                    id_radio=radio_id,
                    data_str=date_iso,
                    time_str=time_val,
                    artist=artist,
                    title=title,
                    source='SCRAPER_RETRO',
                    duration=240
                )
                inserted_count += 1
            count += 1

        return True, f"Scraping completato! Trovati ed inseriti {inserted_count} passaggi per la data {date_iso}."

    except Exception as e:
        print(f"[ERRORE] Durante lo scraping: {e}")
        return False, f"Errore durante lo scraping: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python scraper_retro.py <ID_Radio> <Data_YYYY-MM-DD>")
        print("Esempio: python scraper_retro.py subasio 2026-06-15")
        sys.exit(1)
        
    radio = sys.argv[1]
    date_arg = sys.argv[2]
    
    success, msg = scrape_retro(radio, date_arg)
    print(msg)
