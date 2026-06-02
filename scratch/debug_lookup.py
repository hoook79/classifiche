import os
import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Let's copy normalize_name from genera_html.py
def normalize_name(s):
    s = s.lower().strip()
    s = re.sub(r'\s*\(\d{4}\)\s*$', '', s)
    s = re.sub(r'\s*\(\d{4}\)', '', s)
    
    if ' - ' in s:
        parts = s.split(' - ', 1)
        artist_part = parts[0].strip()
        title_part = parts[1].strip()
    else:
        artist_part = ''
        title_part = s.strip()
        
    sep_pattern = r'\bfeat\.?\b|\bft\.?\b|\bfeaturing\b|&|\be\b|\band\b|,'
    artists = re.split(sep_pattern, artist_part)
    
    cleaned_artists = []
    for art in artists:
        art_clean = re.sub(r'[^a-z0-9]', '', art)
        if art_clean:
            cleaned_artists.append(art_clean)
            
    cleaned_artists.sort()
    canonical_artist = "".join(cleaned_artists)
    canonical_title = re.sub(r'[^a-z0-9]', '', title_part)
    
    if canonical_artist:
        return f"{canonical_artist}|{canonical_title}"
    else:
        return canonical_title

# Load radiodates
with open('song_radiodates_cache.json', 'r', encoding='utf-8') as f:
    radiodates_cache = json.load(f)

normalized_radiodates_cache = {normalize_name(k): v for k, v in radiodates_cache.items() if v != 'N/A' and v != 'N/D'}

test_songs = [
    "TIZIANO FERRO, GIORGIA - Superstar",
    "Tiziano Ferro Feat. Giorgia - Superstar",
    "Giorgia, Tiziano Ferro - Superstar",
    "Tiziano Ferro & Giorgia - Superstar"
]

print("Check lookups:")
for s in test_songs:
    norm = normalize_name(s)
    val = normalized_radiodates_cache.get(norm, 'MISSING')
    print(f"  '{s}' -> norm: '{norm}' -> date: {val}")

# Let's inspect some of the actual keys in normalized_radiodates_cache
print("\nFirst 10 keys in normalized_radiodates_cache:")
for k, v in list(normalized_radiodates_cache.items())[:10]:
    print(f"  {k} -> {v}")
