import sys
import os
sys.path.append(r'c:\Users\Jonny\Desktop\REPORT CANZONI RADIO')

from fetch_years import is_valid_year_for_song, split_artist_title, get_year_from_musicbrainz, get_year_from_itunes, get_year_from_genius, get_year_from_wikipedia

print("=== AVVIO TEST DI RESILIENZA E VALIDAZIONE ===\n")

test_cases = [
    ("ANNALISA - L'Ultimo Addio", "2014", True),
    ("TIZIANO FERRO FEAT. LAZZA - XXDONO", "1984", False),
    ("TIZIANO FERRO FEAT. LAZZA - XXDONO", "2026", True),
    ("MARCO MENGONI - Dove Si Vola", "2009", True),
    ("MR RAIN - LUNEDI' NERO", "2008", False),
    ("TAKAGI & KETRA, MARCO MENGONI, FRAH QUINTALE - Venere E Marte", "1997", False),
    ("TAKAGI & KETRA, MARCO MENGONI, FRAH QUINTALE - Venere E Marte", "2021", True),
]

all_passed = True
for song, year, expected in test_cases:
    res = is_valid_year_for_song(song, year)
    status = "OK" if res == expected else "FALLITO"
    print(f"Brano: '{song}' | Anno: {year} | Risultato: {res} (Atteso: {expected}) -> {status}")
    if res != expected:
        all_passed = False

print(f"\nEsito complessivo test di validazione: {'TUTTI PASSATI' if all_passed else 'CI SONO ERRORI'}")

print("\n=== TEST DI RICERCA ATTIVA API SU CASI ANOMALI ===")
# Facciamo una prova di ricerca per vedere cosa trovano effettivamente le API
problematic_songs = [
    "ANNALISA - L'Ultimo Addio",
    "TIZIANO FERRO FEAT. LAZZA - XXDONO",
    "MARCO MENGONI - Dove Si Vola",
    "MR RAIN - LUNEDI' NERO"
]

for song in problematic_songs:
    print(f"\nTest per: '{song}'")
    
    print("Tentativo MusicBrainz...")
    mb = get_year_from_musicbrainz(song)
    print(f"  -> MusicBrainz ha restituito: {mb}")
    if mb != "N/A":
        print(f"  -> Validità: {is_valid_year_for_song(song, mb)}")
        
    print("Tentativo iTunes...")
    it = get_year_from_itunes(song)
    print(f"  -> iTunes ha restituito: {it}")
    if it != "N/A":
        print(f"  -> Validità: {is_valid_year_for_song(song, it)}")
        
    print("Tentativo Genius...")
    gn = get_year_from_genius(song)
    print(f"  -> Genius ha restituito: {gn}")
    if gn != "N/A":
        print(f"  -> Validità: {is_valid_year_for_song(song, gn)}")
        
    print("Tentativo Wikipedia...")
    wk = get_year_from_wikipedia(song)
    print(f"  -> Wikipedia ha restituito: {wk}")
    if wk != "N/A":
        print(f"  -> Validità: {is_valid_year_for_song(song, wk)}")
