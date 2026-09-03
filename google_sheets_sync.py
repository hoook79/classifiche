#!/usr/bin/env python3
import os
import json
from db_manager import get_db_connection

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
        active_radios = ["all"]

        # Mappatura per la formattazione corretta dei nomi delle radio
        capitalized_labels = {
            "subasio": "Subasio",
            "divina": "Divina",
            "mitology": "Mitology",
            "nostalgia": "Nostalgia",
            "toscana": "Toscana",
            "italia": "Italia",
            "rds": "RDS",
            "rtl1025": "RTL1025",
            "birikina": "Birikina",
            "bruno": "Bruno",
            "kisskiss": "Kisskiss",
            "m2o": "M2o",
            "propostaaosta": "Propostaaosta",
            "capital": "Capital"
        }

        for radio_key, data in all_radio_data.items():
            formatted_name = capitalized_labels.get(radio_key.lower(), radio_key.capitalize())
            sheet_name = f"Data_{formatted_name}"
            songs = data.get('songs', [])
            dates = data.get('dates', [])
            
            # Salva le date per questa radio nei metadati
            dates_metadata.append([radio_key, json.dumps(dates)])
            active_radios.append(formatted_name)

            print(f"  Aggiornamento scheda '{sheet_name}' con {len(songs)} brani...")
            
            # Cerca la scheda esistente in modo case-insensitive per evitare conflitti e correggerne il nome se necessario
            sheet = None
            for w in spreadsheet.worksheets():
                if w.title.lower() == sheet_name.lower():
                    sheet = w
                    if w.title != sheet_name:
                        w.update_title(sheet_name)
                        print(f"  Rinominata scheda '{w.title}' -> '{sheet_name}' per correzione maiuscole/minuscole.")
                    break
            
            if sheet is None:
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

        # Aggiorna la tabella Active_Radios per consentire la convalida da intervallo
        print("  Aggiornamento elenco delle radio attive...")
        try:
            active_sheet = spreadsheet.worksheet("Active_Radios")
        except gspread.exceptions.WorksheetNotFound:
            active_sheet = spreadsheet.add_worksheet(title="Active_Radios", rows="50", cols="1")
        
        active_rows = [["Radio"]] + [[r] for r in active_radios]
        active_sheet.clear()
        active_sheet.update(f"A1:A{len(active_rows)}", active_rows)
        print("  [OK] Elenco delle radio attive aggiornato.")

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

def sync_metadata():
    """
    Sincronizza bidirezionalmente i metadati delle canzoni tra il database locale SQLite e Google Sheets.
    1. Scarica i metadati modificati online su Google Sheets ed aggiorna il database locale.
    2. Carica i metadati locali su Google Sheets (comprese le canzoni appena arricchite).
    """
    client = get_sheets_client()
    if not client:
        return
        
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        print("\n[GOOGLE SHEETS] Sincronizzazione metadati canzoni...")
        spreadsheet = client.open(SPREADSHEET_NAME)
        
        # Cerca o crea la scheda CanzoniMetadati
        sheet_name = "CanzoniMetadati"
        try:
            sheet = spreadsheet.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            sheet = spreadsheet.add_worksheet(title=sheet_name, rows="1000", cols="9")
            print(f"  [INFO] Scheda '{sheet_name}' creata su Google Sheets.")

        # --- STEP 1: SCARICA DA GOOGLE SHEETS ED AGGIORNA DB LOCALE ---
        records = sheet.get_all_records()
        online_count = 0
        if records:
            print(f"  Analisi di {len(records)} record da Google Sheets...")
            # Recupera metadati locali correnti per confronto
            cursor.execute("SELECT artista_pulito, titolo_pulito, codice_siae, codice_iswc, codice_isrc, compositore, autore, casa_discografica, anno_pubblicazione FROM canzoni_metadati")
            local_map = {}
            for r in cursor.fetchall():
                key = (r["artista_pulito"].strip().lower(), r["titolo_pulito"].strip().lower())
                local_map[key] = dict(r)
                
            # Aggiorna localmente se i dati online sono più compilati o diversi
            for r in records:
                art = str(r.get("Artista", "")).strip()
                tit = str(r.get("Titolo", "")).strip()
                if not art or not tit:
                    continue
                    
                key = (art.lower(), tit.lower())
                
                siae = str(r.get("SIAE", "")).strip()
                iswc = str(r.get("ISWC", "")).strip()
                isrc = str(r.get("ISRC", "")).strip()
                comp = str(r.get("Compositore", "")).strip()
                aut = str(r.get("Autore", "")).strip()
                label = str(r.get("CasaDiscografica", "")).strip()
                year = str(r.get("Anno", "")).strip()
                
                local_song = local_map.get(key)
                needs_update = False
                
                if local_song:
                    def val_changed(online_val, local_val):
                        if online_val and online_val != local_val:
                            return True
                        return False
                        
                    if val_changed(siae, local_song["codice_siae"]) or \
                       val_changed(iswc, local_song["codice_iswc"]) or \
                       val_changed(isrc, local_song["codice_isrc"]) or \
                       val_changed(comp, local_song["compositore"]) or \
                       val_changed(aut, local_song["autore"]) or \
                       val_changed(label, local_song["casa_discografica"]) or \
                       val_changed(year, local_song["anno_pubblicazione"]):
                        needs_update = True
                else:
                    needs_update = True
                    
                if needs_update:
                    final_siae = siae if siae else (local_song["codice_siae"] if local_song else "")
                    final_iswc = iswc if iswc else (local_song["codice_iswc"] if local_song else "")
                    final_isrc = isrc if isrc else (local_song["codice_isrc"] if local_song else "")
                    final_comp = comp if comp else (local_song["compositore"] if local_song else "")
                    final_aut = aut if aut else (local_song["autore"] if local_song else "")
                    final_label = label if label else (local_song["casa_discografica"] if local_song else "")
                    final_year = year if year else (local_song["anno_pubblicazione"] if local_song else "")
                    
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
                    ''', (art, tit, final_siae, final_iswc, final_isrc, final_comp, final_aut, final_label, final_year))
                    online_count += 1
                    
            if online_count > 0:
                conn.commit()
                print(f"  [OK] Applicati {online_count} aggiornamenti da Google Sheets al DB locale.")
                
        # --- STEP 2: CARICA TUTTI I DATI DA DB LOCALE A GOOGLE SHEETS ---
        cursor.execute("SELECT artista_pulito, titolo_pulito, codice_siae, codice_iswc, codice_isrc, compositore, autore, casa_discografica, anno_pubblicazione FROM canzoni_metadati ORDER BY artista_pulito, titolo_pulito")
        all_local = cursor.fetchall()
        
        rows = [["Artista", "Titolo", "SIAE", "ISWC", "ISRC", "Compositore", "Autore", "CasaDiscografica", "Anno"]]
        for r in all_local:
            rows.append([
                r["artista_pulito"],
                r["titolo_pulito"],
                r["codice_siae"] or "",
                r["codice_iswc"] or "",
                r["codice_isrc"] or "",
                r["compositore"] or "",
                r["autore"] or "",
                r["casa_discografica"] or "",
                r["anno_pubblicazione"] or ""
            ])
            
        print(f"  Caricamento di {len(rows)-1} metadati canzoni su Google Sheets...")
        sheet.clear()
        
        range_name = f"A1:I{len(rows)}"
        sheet.update(range_name, rows)
        print("  [OK] Scheda 'CanzoniMetadati' aggiornata con i dati locali.")
        
    except Exception as e:
        print(f"[GOOGLE SHEETS] Errore durante la sincronizzazione dei metadati: {e}")
    finally:
        conn.close()
