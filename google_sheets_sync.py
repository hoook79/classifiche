#!/usr/bin/env python3
import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.path.join(BASE_DIR, 'google_credentials.json')
SPREADSHEET_NAME = "RadioCharts_Database"  # Puoi cambiare il nome del foglio qui

# Tentativo di importare gspread e oauth2client
GSPREAD_AVAILABLE = False
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    GSPREAD_AVAILABLE = True
except ImportError:
    pass

def get_sheets_client():
    if not GSPREAD_AVAILABLE:
        print("\n[GOOGLE SHEETS] ERRORE: Librerie 'gspread' o 'oauth2client' non installate.")
        print("Esegui: pip install gspread oauth2client")
        return None
        
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"\n[GOOGLE SHEETS] ATTENZIONE: File credenziali '{CREDENTIALS_FILE}' non trovato.")
        print("La sincronizzazione con Google Sheets verrà saltata.")
        return None

    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        print(f"\n[GOOGLE SHEETS] Errore durante l'autenticazione delle API Google: {e}")
        return None

def download_overrides():
    """Scarica gli override degli anni e delle radio date da Google Sheets e li salva in locale"""
    client = get_sheets_client()
    if not client:
        return

    try:
        print("\n[GOOGLE SHEETS] Download degli override da Google Sheets...")
        spreadsheet = client.open(SPREADSHEET_NAME)
        
        # 1. Anni (YearsCache)
        try:
            years_sheet = spreadsheet.worksheet("YearsCache")
            years_records = years_sheet.get_all_records()
            years_override = {}
            for r in years_records:
                key = r.get("SongKey")
                val = r.get("Year")
                if key and val:
                    years_override[str(key).strip()] = str(val).strip()
            
            override_file = os.path.join(BASE_DIR, 'manual_years_override.json')
            with open(override_file, 'w', encoding='utf-8') as f:
                json.dump(years_override, f, indent=2, ensure_ascii=False)
            print(f"  [OK] Scaricati {len(years_override)} override per gli anni.")
        except gspread.exceptions.WorksheetNotFound:
            print("  [INFO] Tabella 'YearsCache' non ancora presente su Google Sheets.")

        # 2. Radio Dates (RadioDatesCache)
        try:
            rd_sheet = spreadsheet.worksheet("RadioDatesCache")
            rd_records = rd_sheet.get_all_records()
            rd_override = {}
            for r in rd_records:
                key = r.get("SongKey")
                val = r.get("RadioDate")
                if key and val:
                    rd_override[str(key).strip()] = str(val).strip()
            
            rd_override_file = os.path.join(BASE_DIR, 'manual_radiodates_override.json')
            with open(rd_override_file, 'w', encoding='utf-8') as f:
                json.dump(rd_override, f, indent=2, ensure_ascii=False)
            print(f"  [OK] Scaricati {len(rd_override)} override per le radio date.")
        except gspread.exceptions.WorksheetNotFound:
            print("  [INFO] Tabella 'RadioDatesCache' non ancora presente su Google Sheets.")

    except Exception as e:
        print(f"[GOOGLE SHEETS] Errore durante il download degli override: {e}")

def upload_rankings(all_radio_data):
    """
    Carica i dati elaborati delle classifiche su Google Sheets.
    all_radio_data è un dizionario: { 'subasio': { 'songs': [...], 'dates': [...] }, ... }
    """
    client = get_sheets_client()
    if not client:
        return

    try:
        print("\n[GOOGLE SHEETS] Caricamento delle classifiche su Google Sheets...")
        spreadsheet = client.open(SPREADSHEET_NAME)
        
        dates_metadata = []

        for radio_key, data in all_radio_data.items():
            sheet_name = f"Data_{radio_key.capitalize()}"
            songs = data.get('songs', [])
            dates = data.get('dates', [])
            
            # Salva le date per questa radio nei metadati
            dates_metadata.append([radio_key, json.dumps(dates)])

            print(f"  Aggiornamento scheda '{sheet_name}' con {len(songs)} brani...")
            
            # Cerca o crea la scheda per questa radio
            try:
                sheet = spreadsheet.worksheet(sheet_name)
            except gspread.exceptions.WorksheetNotFound:
                sheet = spreadsheet.add_worksheet(title=sheet_name, rows="1000", cols="7")

            # Costruisci la tabella dei dati
            # Intestazioni: Rank, Artist, Title, Year, RadioDate, Total, Days
            rows = [["Rank", "Artist", "Title", "Year", "RadioDate", "Total", "Days"]]
            for s in songs:
                rows.append([
                    s.get('rank', 0),
                    s.get('artist', ''),
                    s.get('title', ''),
                    s.get('year', 'N/A'),
                    s.get('radioDate', 'N/A'),
                    s.get('total', 0),
                    json.dumps(s.get('days', {}))  # Stringa JSON per i passaggi dettagliati
                ])

            # Pulisci la scheda precedente e scrivi i nuovi dati
            sheet.clear()
            
            # Carica i dati a blocchi per evitare timeout o limiti di API
            # Se ci sono molti brani, usiamo update con range completo
            range_name = f"A1:{gspread.utils.rowcol_to_a1(len(rows), 7)}"
            sheet.update(range_name, rows)
            print(f"  [OK] Scheda '{sheet_name}' aggiornata.")

        # Aggiorna la tabella Dates_Metadata
        print("  Aggiornamento metadati delle date...")
        try:
            meta_sheet = spreadsheet.worksheet("Dates_Metadata")
        except gspread.exceptions.WorksheetNotFound:
            meta_sheet = spreadsheet.add_worksheet(title="Dates_Metadata", rows="20", cols="2")
        
        meta_rows = [["Radio", "DatesList"]] + dates_metadata
        meta_sheet.clear()
        meta_sheet.update(f"A1:B{len(meta_rows)}", meta_rows)
        print("  [OK] Metadati delle date aggiornati.")
        print("[GOOGLE SHEETS] Sincronizzazione completata con successo!")

    except Exception as e:
        print(f"[GOOGLE SHEETS] Errore durante il caricamento dei dati: {e}")
