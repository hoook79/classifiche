import json
import os
import re
from collections import Counter

sys_path = r"c:\Users\Jonny\Desktop\REPORT CANZONI RADIO"
history_files = [
    'radio_subasio_history.json',
    'radio_divina_history.json',
    'radio_mitology_history.json',
    'radio_nostalgia_history.json',
    'radio_toscana_history.json',
    'radio_italia_history.json',
    'radio_rds_history.json',
    'radio_rtl1025_history.json'
]

artists = []

def split_artist_title(song_query):
    if " - " in song_query:
        parts = song_query.split(" - ", 1)
        return parts[0].strip()
    return song_query.strip()

for f_name in history_files:
    path = os.path.join(sys_path, f_name)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item in data:
                song = item.get('song', '')
                song_no_year = re.sub(r'\s*\(\d{4}\)\s*$', '', song).strip()
                artist = split_artist_title(song_no_year)
                artists.append(artist.upper())

counts = Counter(artists)
print("Top 100 artists in history files:")
for artist, count in counts.most_common(100):
    print(f"  {artist}: {count}")
