#!/usr/bin/env python3
import re
import csv
from io import StringIO
from db_manager import insert_passage

def parse_log_line(line):
    """
    Tenta di analizzare una singola riga di log usando formati comuni.
    Ritorna (date_str, time_str, artist, title) se ha successo, altrimenti None.
    """
    line = line.strip()
    if not line:
        return None

    # Pattern 1: MB Studio Standard -> DD-MM-YYYY HH:MM:SS|TITOLO|ARTISTA
    # es: 16-06-2026 13:00:00|Canzone|Artista
    match = re.match(r'^(\d{2}[-/.]\d{2}[-/.]\d{4})\s+(\d{2}:\d{2}:\d{2})\|(.*?)\|(.*?)$', line)
    if match:
        d, t, title, artist = match.groups()
        return d, t, artist.strip(), title.strip()

    # Pattern 2: MB Studio Variato -> DD-MM-YYYY HH:MM:SS|ARTISTA|TITOLO
    # es: 16-06-2026 13:00:00|Artista|Canzone
    # Se il primo campo dopo la data contiene caratteri tipici di titoli/artisti, o se vogliamo supportare entrambi.
    # Assumiamo standard MB Studio come TITOLO|ARTISTA (come da richiesta).

    # Pattern 3: DJ Pro Standard con trattino -> DD-MM-YYYY HH:MM:SS - TITOLO - ARTISTA
    # es: 16-06-2026 13:00:00 - Titolo Canzone - Nome Artista
    match = re.match(r'^(\d{2}[-/.]\d{2}[-/.]\d{4})\s+(\d{2}:\d{2}:\d{2})\s+-\s+(.*?)\s+-\s+(.*?)$', line)
    if match:
        d, t, title, artist = match.groups()
        return d, t, artist.strip(), title.strip()

    # Pattern 4: Alternativo DJ Pro -> DD-MM-YYYY HH:MM:SS - ARTISTA - TITOLO
    # es: 16-06-2026 13:00:00 - Nome Artista - Titolo Canzone
    # In molti casi DJ Pro scrive ARTISTA - TITOLO. Per essere universali,
    # se non c'è una separazione esplicita o se è separato da ";", proviamo ad analizzarlo sotto.

    # Proviamo split generico con separatori comuni
    for sep in [';', '|', '\t']:
        parts = line.split(sep)
        if len(parts) >= 3:
            # Controlla se il primo elemento contiene una data ed ora
            dt_part = parts[0].strip()
            # Cerca data e ora in dt_part
            date_match = re.search(r'(\d{2}[-/.]\d{2}[-/.]\d{4})', dt_part)
            time_match = re.search(r'(\d{2}:\d{2}(:\d{2})?)', dt_part)
            
            if date_match and time_match:
                d = date_match.group(1)
                t = time_match.group(1)
                
                # Solitamente: parte 1 = Titolo, parte 2 = Artista
                # ma se ci sono più parti, prendi le prime due disponibili
                title = parts[1].strip()
                artist = parts[2].strip()
                return d, t, artist, title

    # Proviamo split con trattino generico se contiene un timestamp all'inizio
    # es: 16-06-2026 13:00:00 - Artista - Titolo
    dt_match = re.match(r'^(\d{2}[-/.]\d{2}[-/.]\d{4})\s+(\d{2}:\d{2}(:\d{2})?)\s*[-–—:]\s*(.*)$', line)
    if dt_match:
        d, t, _, rest = dt_match.groups()
        parts = rest.split(' - ')
        if len(parts) >= 2:
            # Se ha 2 parti: assumiamo prima Titolo poi Artista, o viceversa.
            # MB Studio e DJ Pro usano solitamente TITOLO - ARTISTA o viceversa.
            # Proviamo a restituire quello che troviamo.
            return d, t, parts[1].strip(), parts[0].strip()

    return None

def parse_log_file(file_content, id_radio):
    """
    Parsa l'intero file log (sia CSV che testo) e lo inserisce nel database.
    Ritorna il numero di righe inserite con successo.
    """
    lines = file_content.splitlines()
    inserted_count = 0
    
    # 1. Controlla se sembra un CSV strutturato
    # Se la prima riga contiene intestazioni come "artista", "titolo", "date"
    first_line = lines[0].lower() if lines else ""
    is_csv_with_header = any(x in first_line for x in ['titolo', 'title', 'artista', 'artist', 'song', 'canzone']) and (';' in first_line or ',' in first_line)
    
    if is_csv_with_header:
        # Parsa come CSV
        f = StringIO(file_content)
        # Rileva dialetto (spesso semicolon in Italia)
        delimiter = ';' if ';' in first_line else ','
        reader = csv.DictReader(f, delimiter=delimiter)
        
        for row in reader:
            # Cerca le colonne di interesse in modo flessibile
            date_val, time_val, artist, title = None, None, None, None
            
            for k, v in row.items():
                if not k:
                    continue
                k_lower = k.lower()
                if 'data' in k_lower or 'date' in k_lower:
                    date_val = v
                elif 'ora' in k_lower or 'time' in k_lower:
                    time_val = v
                elif 'artista' in k_lower or 'artist' in k_lower:
                    artist = v
                elif 'titolo' in k_lower or 'title' in k_lower or 'song' in k_lower or 'canzone' in k_lower:
                    title = v
            
            # Se ha trovato le colonne minime
            if date_val and artist and title:
                # Se l'ora non è in colonna separata, potrebbe essere incorporata nella data
                if not time_val:
                    dt_match = re.search(r'(\d{2}:\d{2}(:\d{2})?)', date_val)
                    if dt_match:
                        time_val = dt_match.group(1)
                
                # Pulisci e normalizza
                try:
                    insert_passage(
                        id_radio=id_radio,
                        data_str=date_val.strip(),
                        time_str=time_val.strip() if time_val else "00:00:00",
                        artist=artist.strip(),
                        title=title.strip(),
                        source='IMPORT_LOG',
                        duration=240
                    )
                    inserted_count += 1
                except Exception as e:
                    print(f"Errore inserimento riga CSV: {e}")
        return inserted_count
        
    # 2. Parsa come file di testo riga per riga
    for line in lines:
        parsed = parse_log_line(line)
        if parsed:
            d, t, artist, title = parsed
            try:
                insert_passage(
                    id_radio=id_radio,
                    data_str=d,
                    time_str=t,
                    artist=artist,
                    title=title,
                    source='IMPORT_LOG',
                    duration=240
                )
                inserted_count += 1
            except Exception as e:
                print(f"Errore inserimento riga log: {e}")
                
    return inserted_count

if __name__ == "__main__":
    # Semplice test locale
    sample_log = """
16-06-2026 13:05:00|SOLO CON TE|ANTONELLO VENDITTI
16-06-2026 13:09:12|ALBA CHIARA|VASCO ROSSI
16-06-2026 13:13:30 - GLI ANNI - 883
"""
    print("Test parser log:")
    inserted = parse_log_file(sample_log, 'test_radio')
    print(f"Inseriti con successo {inserted} passaggi.")
