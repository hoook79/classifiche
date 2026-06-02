import re
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

def normalize_name(s):
    """
    Super-robust normalization of a song name (format 'Artist - Title' or just 'Title').
    - Lowers the string.
    - Strips years in parentheses like (2026).
    - Splits by ' - ' into artist and title.
    - Standardizes featured artist tags, conjunctions, and delimiters.
    - Sorts multiple artists alphabetically so order doesn't matter.
    - Returns a canonical key.
    """
    s = s.lower().strip()
    # Strip year in parentheses
    s = re.sub(r'\s*\(\d{4}\)\s*$', '', s)
    s = re.sub(r'\s*\(\d{4}\)', '', s)
    
    if ' - ' in s:
        parts = s.split(' - ', 1)
        artist_part = parts[0].strip()
        title_part = parts[1].strip()
    else:
        artist_part = ''
        title_part = s.strip()
        
    # Normalize artist part
    # Split artists by typical separators: feat, feat., ft, ft., featuring, &, e, and, comma
    # Note: " e " is Italian "and"
    sep_pattern = r'\bfeat\.?\b|\bft\.?\b|\bfeaturing\b|&|\be\b|\band\b|,'
    artists = re.split(sep_pattern, artist_part)
    
    cleaned_artists = []
    for art in artists:
        # Strip all punctuation and whitespace from each artist name
        art_clean = re.sub(r'[^a-z0-9]', '', art)
        if art_clean:
            cleaned_artists.append(art_clean)
            
    # Sort artists alphabetically
    cleaned_artists.sort()
    canonical_artist = "".join(cleaned_artists)
    
    # Normalize title part: strip non-alphanumeric
    canonical_title = re.sub(r'[^a-z0-9]', '', title_part)
    
    if canonical_artist:
        return f"{canonical_artist}|{canonical_title}"
    else:
        return canonical_title

# Test variants
variants = [
    "Tiziano Ferro Feat. Giorgia - Superstar",
    "Tiziano Ferro feat. Giorgia - Superstar",
    "Giorgia, Tiziano Ferro - Superstar",
    "TIZIANO FERRO & GIORGIA - SUPERSTAR",
    "TIZIANO FERRO, GIORGIA - Superstar",
    "TIZIANO FERRO - Superstar (2026)" # wait, if artist is just Tiziano Ferro, it will normalize differently, but that's expected
]

for v in variants:
    print(f"'{v}' -> '{normalize_name(v)}'")

# Let's see if we load the cache and build the normalized lookup
if os.path.exists('song_years_cache.json'):
    with open('song_years_cache.json', 'r', encoding='utf-8') as f:
        cache = json.load(f)
    
    # Build robust lookup
    robust_lookup = {}
    for k, v in cache.items():
        norm_key = normalize_name(k)
        if v != 'N/A':
            robust_lookup[norm_key] = v
            
    print("\nRobust lookup size:", len(robust_lookup))
    # Test lookup for the variants
    print("\nLookup results for variants:")
    for v in variants:
        norm_key = normalize_name(v)
        res = robust_lookup.get(norm_key, 'N/A')
        print(f"  '{v}' -> '{norm_key}' -> {res}")
