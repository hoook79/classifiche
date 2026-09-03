#!/usr/bin/env python3
import re

def clean_text(text):
    if not text:
        return ""
    # Rimuovi spazi extra, spazi uniti, e normalizza
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def clean_song(artist, title):
    """
    Pulisce il nome dell'artista e del titolo dal rumore delle regie.
    Esempio:
      artist="Jovanotti, Alfa", title="Buon Vento (Radio Edit) [2026]"
      -> artist_clean="Jovanotti, Alfa", title_clean="Buon Vento"
    """
    if not artist:
        artist = ""
    if not title:
        title = ""
    
    # 1. Pulizia Titolo
    title_clean = title
    
    # Rimuovi l'anno tra parentesi quadre o tonde alla fine, es: [2026], (2025)
    title_clean = re.sub(r'\[\s*\d{4}\s*\]', '', title_clean)
    title_clean = re.sub(r'\(\s*\d{4}\s*\)', '', title_clean)
    
    # Parole chiave di versioni o edit da ripulire (con parentesi)
    version_patterns_with_parents = [
        r'\(\s*radio\s+edit\s*\)',
        r'\(\s*video\s+(edit|version)?\s*\)',
        r'\(\s*extended\s*(mix|version|edit)?\s*\)',
        r'\(\s*album\s+version\s*\)',
        r'\(\s*single\s*(edit|version)?\s*\)',
        r'\(\s*live\s*(version|edit)?\s*\)',
        r'\(\s*acoustic\s*(version|edit)?\s*\)',
        r'\(\s*original\s*(mix|version|edit)?\s*\)',
        r'\(\s*remastered\s*\)',
        r'\(\s*remaster\s*\)',
        r'\(\s*remix\s*\)',
        r'\(\s*rmx\s*\)',
        r'\(\s*cover\s*\)',
        r'\(\s*tribute\s*\)',
        r'\(\s*mono\s*\)',
        r'\(\s*stereo\s*\)',
    ]
    
    for pattern in version_patterns_with_parents:
        title_clean = re.sub(pattern, '', title_clean, flags=re.IGNORECASE)
        
    # Parole chiave di versioni o edit senza parentesi (es. alla fine della stringa dopo un trattino o virgola)
    # es: "- Radio Edit", "- Remix", "Remix"
    title_clean = re.sub(r'\s*-\s*radio\s+edit\b.*$', '', title_clean, flags=re.IGNORECASE)
    title_clean = re.sub(r'\s*-\s*extended\s*(mix|version)?\b.*$', '', title_clean, flags=re.IGNORECASE)
    title_clean = re.sub(r'\s*-\s*(remix|rmx)\b.*$', '', title_clean, flags=re.IGNORECASE)
    title_clean = re.sub(r'\b(radio\s+edit|extended\s+mix|album\s+version|original\s+mix)\b', '', title_clean, flags=re.IGNORECASE)
    
    # Rimuovi indicazioni feat/ft dal titolo
    # es: "(feat. Coldplay)", "feat. Coldplay", "ft. Coldplay"
    title_clean = re.sub(r'\(\s*(feat|ft|featuring|with)\b.*?\)','', title_clean, flags=re.IGNORECASE)
    title_clean = re.sub(r'\b(feat|ft|featuring|with)\b\.?\s+.*$', '', title_clean, flags=re.IGNORECASE)
    
    # 2. Pulizia Artista
    artist_clean = artist
    # Rimuovi indicazioni feat/ft dall'artista se presenti in coda
    artist_clean = re.sub(r'\b(feat|ft|featuring|with)\b\.?\s+.*$', '', artist_clean, flags=re.IGNORECASE)
    
    # Rimuovi parentesi residue vuote o con soli spazi/punteggiatura
    title_clean = re.sub(r'\(\s*[\-\–\—\s]*\)', '', title_clean)
    title_clean = re.sub(r'\[\s*[\-\–\—\s]*\]', '', title_clean)
    
    # Clean final text
    artist_clean = clean_text(artist_clean)
    title_clean = clean_text(title_clean)
    
    # Se la pulizia ha svuotato il campo, rimetti quello di partenza ripulito dagli spazi
    if not title_clean and title:
        title_clean = clean_text(title)
    if not artist_clean and artist:
        artist_clean = clean_text(artist)
        
    return artist_clean, title_clean

if __name__ == "__main__":
    # Semplici test di verifica
    test_cases = [
        ("Jovanotti, Alfa", "Buon Vento (Radio Edit) [2026]"),
        ("Coldplay Feat. Beyonce", "Hymn For The Weekend (Remix)"),
        ("Dua Lipa", "Levitating (feat. DaBaby)"),
        ("Pink Floyd", "Money - Remastered 2011"),
        ("Gigi D'Agostino", "L'Amour Toujours (Extended Mix)"),
    ]
    print("Test di data_cleaner:")
    for a, t in test_cases:
        ac, tc = clean_song(a, t)
        print(f"Originale: '{a} - {t}' => Pulito: '{ac} - {tc}'")
