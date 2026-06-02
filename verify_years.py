#!/usr/bin/env python3
import json
import os
import re
from datetime import datetime

CACHE_FILE = 'song_years_cache.json'
OVERRIDE_FILE = 'manual_years_override.json'
AUDIT_REPORT = 'song_years_audit.md'

# Artisti con il rispettivo anno di debutto / inizio attività noto.
# Qualsiasi canzone associata a questo artista con anno precedente a questa soglia è considerata un'anomalia.
ARTIST_DEBUT_MAP = {
    'GAZZELLE': 2016,
    'BLANCO': 2020,
    'PINGUINI TATTICI NUCLEARI': 2012,
    'PTN': 2012,
    'TANANAI': 2019,
    'MAHMOOD': 2015,
    'IRAMA': 2015,
    'OLLY': 2019,
    'ACHILLE LAURO': 2012,
    'ANNALISA': 2011,
    'MARCO MENGONI': 2009,
    'TIZIANO FERRO': 2001,
    'LAURA PAUSINI': 1993,
    'EROS RAMAZZOTTI': 1982,
    'NEGRAMARO': 2001,
    'ALF': 2018,  # ALFA
    'ALFA': 2018,
    'COMA COSE': 2017,
    'ANGELINA MANGO': 2020,
    'ULTIMO': 2017,
    'ELODIE': 2015,
    'THE WEEKND': 2010,
    'COLDPLAY': 1998,
    'BEYONCÉ': 1997,
    'ED SHEERAN': 2005,
    'OASIS': 1991,
    '883': 1989,
    'MAX PEZZALI': 1989,
    'VASCO ROSSI': 1977,
    'ZUCCHERO': 1970,
    'LIGABUE': 1987,
    'TOMMASO PARADISO': 2011,
    'THE KOLORS': 2010,
    'SFERA EBBASTA': 2013,
    'LAZZA': 2012,
    'GHALI': 2011,
    'MR RAIN': 2011,
    'MR.RAIN': 2011,
    'ARIETE': 2019,
    'BOOMDABASH': 2002,
    'FEDERICA ABBATE': 2013,
    'ROSE VILLAIN': 2016,
    'GEOLIER': 2018,
    'TEDUA': 2014,
    'CAPO PLAZA': 2016,
    'RONDODASOSA': 2020,
    'MADAME': 2018,
    'ALESSANDRA AMOROSO': 2008,
    'EMMA': 2010,
    'NOEMI': 2009,
    'FULMINACCI': 2019,
    'FRANCESCO GABBANI': 2010,
}

def load_json(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except Exception as e:
                print(f"Errore nel parsing di {filepath}: {e}")
                return {}
    return {}

def split_song(key):
    if " - " in key:
        parts = key.split(" - ", 1)
        return parts[0].strip(), parts[1].strip()
    return "Unknown", key.strip()

def main():
    print("Avvio audit degli anni delle canzoni...")
    
    cache = load_json(CACHE_FILE)
    overrides = load_json(OVERRIDE_FILE)
    
    # Combina cache ed override
    final_years = {}
    for k, v in cache.items():
        final_years[k] = v
    for k, v in overrides.items():
        final_years[k] = v
        
    current_year = datetime.now().year
    
    anomalies = []
    missing_years = []
    valid_count = 0
    override_count = 0
    
    # Raggruppamento per decennio
    decades = {
        'Future (>2026)': [],
        '2020s': [],
        '2010s': [],
        '2000s': [],
        '1990s': [],
        '1980s': [],
        '1970s': [],
        '1960s': [],
        'Pre-1960': [],
        'N/A (Missing)': []
    }
    
    for song_key, year in final_years.items():
        artist, title = split_song(song_key)
        is_override = song_key in overrides
        
        if is_override:
            override_count += 1
            
        if not year or year == "N/A":
            missing_years.append((song_key, artist, title))
            decades['N/A (Missing)'].append((song_key, artist, title, year, is_override))
            continue
            
        # Controlla se è un numero valido
        if not year.isdigit():
            anomalies.append({
                'song': song_key,
                'artist': artist,
                'title': title,
                'year': year,
                'reason': "Anno non numerico",
                'is_override': is_override
            })
            decades['N/A (Missing)'].append((song_key, artist, title, year, is_override))
            continue
            
        y_int = int(year)
        valid_count += 1
        
        # 1. Controlla anni nel futuro
        if y_int > current_year:
            anomalies.append({
                'song': song_key,
                'artist': artist,
                'title': title,
                'year': year,
                'reason': f"Anno nel futuro (> {current_year})",
                'is_override': is_override
            })
            decades['Future (>2026)'].append((song_key, artist, title, year, is_override))
            continue
            
        # 2. Controlla anni troppo vecchi (< 1950)
        if y_int < 1950:
            anomalies.append({
                'song': song_key,
                'artist': artist,
                'title': title,
                'year': year,
                'reason': "Anno precedente al 1950 (estremamente insolito)",
                'is_override': is_override
            })
            
        # 3. Controlla il debutto dell'artista
        artist_upper = artist.upper()
        for a_key, debut_y in ARTIST_DEBUT_MAP.items():
            # Protezione per artisti con nomi simili (es. ANNALISA MINETTI != ANNALISA)
            if a_key == 'ANNALISA' and 'ANNALISA MINETTI' in artist_upper:
                continue
            if a_key == 'OLLY' and 'OLLY MURS' in artist_upper:
                continue
                
            # Match con word boundaries per evitare falsi positivi (es. "OLLY" in "HOLLYWOOD")
            pattern = r'\b' + re.escape(a_key) + r'\b'
            if re.search(pattern, artist_upper):
                if y_int < debut_y:
                    anomalies.append({
                        'song': song_key,
                        'artist': artist,
                        'title': title,
                        'year': year,
                        'reason': f"Anno {year} antecedente al debutto di {a_key} ({debut_y})",
                        'is_override': is_override
                    })
                    break
                    
        # Assegna al decennio corretto
        if y_int >= 2020:
            decades['2020s'].append((song_key, artist, title, year, is_override))
        elif y_int >= 2010:
            decades['2010s'].append((song_key, artist, title, year, is_override))
        elif y_int >= 2000:
            decades['2000s'].append((song_key, artist, title, year, is_override))
        elif y_int >= 1990:
            decades['1990s'].append((song_key, artist, title, year, is_override))
        elif y_int >= 1980:
            decades['1980s'].append((song_key, artist, title, year, is_override))
        elif y_int >= 1970:
            decades['1970s'].append((song_key, artist, title, year, is_override))
        elif y_int >= 1960:
            decades['1960s'].append((song_key, artist, title, year, is_override))
        else:
            decades['Pre-1960'].append((song_key, artist, title, year, is_override))

    # Genera il report in Markdown
    print(f"Generazione report in {AUDIT_REPORT}...")
    with open(AUDIT_REPORT, 'w', encoding='utf-8') as f:
        f.write("# 📻 Report di Audit - Verifica Anni Canzoni\n\n")
        f.write("Questo report analizza automaticamente il database degli anni delle canzoni alla ricerca di incongruenze, anni futuri o incongruenze storiche basate sull'artista.\n\n")
        
        # Sintesi statistica
        f.write("## 📊 Sintesi Statistica\n\n")
        f.write(f"- **Brani Totali in Cache**: `{len(final_years)}`\n")
        f.write(f"- **Brani con Anno Valido**: `{valid_count}`\n")
        f.write(f"- **Brani con Anno Mancante (N/A)**: `{len(missing_years)}`\n")
        f.write(f"- **Correzioni Manuali Applicate**: `{override_count}`\n")
        
        color_alert = "🔴" if anomalies else "🟢"
        f.write(f"- **Anomalie Rilevate**: {color_alert} `{len(anomalies)}`\n\n")
        
        # Sezione Anomalie Rilevate
        f.write("## ⚠️ Anomalie e Sospetti Rilevati\n")
        f.write("Questi brani presentano anni che sono storicamente impossibili o palesemente errati. **Dovresti correggerli aggiungendoli a `manual_years_override.json`.**\n\n")
        
        if anomalies:
            f.write("| Stato | Canzone | Anno Rilevato | Causa dell'Anomalia | Tipo |\n")
            f.write("| :---: | :--- | :---: | :--- | :---: |\n")
            for an in anomalies:
                status = "✍️" if an['is_override'] else "❌"
                typ = "Override" if an['is_override'] else "Automatico"
                f.write(f"| {status} | **{an['artist']}** - {an['title']} | `{an['year']}` | {an['reason']} | {typ} |\n")
        else:
            f.write("> **Nessuna anomalia grave rilevata!** Ottimo lavoro.\n")
        f.write("\n---\n\n")
        
        # Sezione Override Manuali
        f.write("## ✍️ Correzioni Manuali Attive (`manual_years_override.json`)\n")
        f.write("Elenco dei brani corretti manualmente che sono bloccati contro futuri aggiornamenti degli script automatici:\n\n")
        if overrides:
            f.write("| Canzone | Anno Forzato |\n")
            f.write("| :--- | :---: |\n")
            for k, v in sorted(overrides.items()):
                f.write(f"| {k} | **`{v}`** |\n")
        else:
            f.write("> *Nessun override manuale attualmente configurato.*\n")
        f.write("\n---\n\n")
        
        # Elenco completo per decenni
        f.write("## 📂 Libreria Completa per Decenni\n")
        f.write("Scorri questa lista per individuare rapidamente ad occhio canzoni posizionate nel decennio sbagliato.\n\n")
        
        for decade, items in decades.items():
            if not items:
                continue
            f.write(f"### 📅 {decade} ({len(items)} brani)\n\n")
            f.write("| Canzone | Anno | Tipo |\n")
            f.write("| :--- | :---: | :---: |\n")
            # Ordina per artista e poi per titolo
            sorted_items = sorted(items, key=lambda x: (x[1].lower(), x[2].lower()))
            for song_key, artist, title, year, is_override in sorted_items:
                marker = "✍️ Override" if is_override else "Auto"
                f.write(f"| **{artist}** - {title} | `{year}` | *{marker}* |\n")
            f.write("\n")
            
    print(f"Audit completato con successo! Trovate {len(anomalies)} anomalie. Report generato in {AUDIT_REPORT}.")

if __name__ == "__main__":
    main()
