import requests
import urllib.parse

artist = "Annalisa"
title = "Sinceramente"
query = f'track:"{title}" artist:"{artist}"'
encoded = urllib.parse.quote(query)
url = f"https://api.deezer.com/search?q={encoded}"

r = requests.get(url)
if r.status_code == 200:
    data = r.json()
    items = data.get("data", [])
    if items:
        track = items[0]
        print("Keys returned by search:", track.keys())
        # Controlla se c'è isrc
        print("ISRC da ricerca:", track.get("isrc"))
        # Se c'è un campo track, prendi id e interroga dettagli
        track_id = track.get("id")
        if track_id:
            r_details = requests.get(f"https://api.deezer.com/track/{track_id}")
            if r_details.status_code == 200:
                det = r_details.json()
                print("Dettagli track keys:", det.keys())
                print("ISRC da dettagli:", det.get("isrc"))
                print("Release Date da dettagli:", det.get("release_date"))
                # Etichetta: si trova nell'album o in track?
                print("Etichetta/Label o casa discografica?:", det.get("contributors"), det.get("artist"), det.get("album"))
    else:
        print("Nessun risultato trovato per la ricerca avanzata, provo semplice...")
        url_simple = f"https://api.deezer.com/search?q={urllib.parse.quote(artist + ' ' + title)}"
        r = requests.get(url_simple)
        if r.status_code == 200:
            items = r.json().get("data", [])
            if items:
                track = items[0]
                track_id = track.get("id")
                r_details = requests.get(f"https://api.deezer.com/track/{track_id}")
                if r_details.status_code == 200:
                    det = r_details.json()
                    print("ISRC da dettagli semplice:", det.get("isrc"))
                    print("Label da dettagli semplice:", det.get("label"))
                    print("Release Date da dettagli semplice:", det.get("release_date"))
else:
    print("Errore HTTP:", r.status_code)
