import requests
import urllib.parse
import re

artist = "Annalisa"
title = "Canzone Estiva"
query = f"{artist} {title}"
url = f"https://itunes.apple.com/search?term={urllib.parse.quote(query)}&media=music&limit=1"

r = requests.get(url)
print("Status:", r.status_code)
if r.status_code == 200:
    data = r.json()
    results = data.get("results", [])
    if results:
        track = results[0]
        print("Track Name:", track.get("trackName"))
        print("Artist Name:", track.get("artistName"))
        print("Collection Name (Album):", track.get("collectionName"))
        print("Release Date:", track.get("releaseDate"))
        
        # Vediamo se c'è la label (spesso in copyright nell'album o in altri campi)
        # iTunes a volte non restituisce il copyright a livello di traccia se non interroghiamo l'album
        album_id = track.get("collectionId")
        print("Album ID:", album_id)
        print("Track Keys:", track.keys())
        
        if album_id:
            album_url = f"https://itunes.apple.com/lookup?id={album_id}"
            ar = requests.get(album_url)
            if ar.status_code == 200:
                album_data = ar.json().get("results", [])
                if album_data:
                    album = album_data[0]
                    print("\nAlbum Copyright:", album.get("copyright"))
                    print("Album Keys:", album.keys())
    else:
        print("No results")
