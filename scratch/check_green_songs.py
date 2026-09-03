import sqlite3

conn = sqlite3.connect('radio_reports.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Seleziona le canzoni arricchite con ISRC
cursor.execute("SELECT * FROM canzoni_metadati WHERE codice_isrc != '' LIMIT 5")
rows = cursor.fetchall()
for r in rows:
    print(f"Artista: {r['artista_pulito']}, Titolo: {r['titolo_pulito']}")
    print(f"  ISRC: {r['codice_isrc']}")
    print(f"  ISWC: {r['codice_iswc']}")
    print(f"  Compositore: {r['compositore']}")
    print(f"  Autore: {r['autore']}")
    print(f"  Label: {r['casa_discografica']}")
    print(f"  Anno: {r['anno_pubblicazione']}")
    
    # Valuta semaforo
    def is_empty(val):
        return not val or val.strip() in ['', '-', 'N/A', 'N/D']

    has_siae = not is_empty(r["codice_siae"])
    has_isrc = not is_empty(r["codice_isrc"])
    has_iswc = not is_empty(r["codice_iswc"])
    has_writer = not (is_empty(r["compositore"]) and is_empty(r["autore"]))
    has_label_or_year = not (is_empty(r["casa_discografica"]) and is_empty(r["anno_pubblicazione"]))
    
    status = "YELLOW"
    if (has_siae or has_iswc) and has_isrc and has_writer and has_label_or_year:
        status = "GREEN 🟢"
    elif not has_siae and not has_iswc and not has_isrc and not has_writer and not has_label_or_year:
        status = "RED 🔴"
        
    print(f"  Status calcolato: {status}\n")

conn.close()
