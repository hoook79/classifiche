import requests
import json
import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

def _norm(s):
    import unicodedata as _ud
    s = (s or '').lower()
    s = _ud.normalize('NFD', s)
    s = ''.join(c for c in s if _ud.category(c) != 'Mn')
    s = re.sub(r'[^a-z0-9 ]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()

def _score_pair(r_artist, r_title, q_artist, q_title):
    ra, rt = _norm(r_artist), _norm(r_title)
    al, tl = _norm(q_artist), _norm(q_title)
    sa = 8 if ra == al else (5 if (al in ra or ra in al) else
         sum(2 for w in al.split() if len(w) > 2 and w in ra))
    st = 8 if rt == tl else (5 if (tl in rt or rt in tl) else
         sum(2 for w in tl.split() if len(w) > 2 and w in rt))
    return sa, st

def split_artist_title(song_query):
    if " - " in song_query:
        parts = song_query.split(" - ", 1)
        return parts[0].strip(), parts[1].strip()
    return None, song_query.strip()

def get_mb_artist_name(rec):
    credits = rec.get("artist-credit", [])
    parts = []
    for c in credits:
        parts.append(c.get("name", ""))
        if "joinphrase" in c:
            parts.append(c["joinphrase"])
    return "".join(parts).strip()

def get_year_from_musicbrainz_scored(song_query):
    api_url = "https://musicbrainz.org/ws/2/recording"
    headers = {"User-Agent": "RadioMonitor/2.0 (mailto:radio@monitor.it)"}

    artist, title = split_artist_title(song_query)
    if not artist or not title:
        return "N/A"

    title_clean = re.sub(r'[+\-&|!(){}\[\]^"~*?:\\]', ' ', title).strip()
    artist_clean = re.sub(r'[+\-&|!(){}\[\]^"~*?:\\]', ' ', artist).strip()
    artist_clean = artist_clean.split(",")[0].strip()
    
    queries = [
        f'recording:"{title_clean}" AND artist:"{artist_clean}"',
        f'recording:"{title_clean}" AND artistname:"{artist_clean}"',
        f'{title_clean} {artist_clean}',
    ]

    best_score = -1
    best_year = "N/A"

    for query in queries:
        params = {
            "query": query,
            "fmt": "json",
            "limit": 10
        }
        try:
            r = requests.get(api_url, params=params, headers=headers, timeout=10)
            if r.status_code != 200:
                continue
            recordings = r.json().get("recordings", [])

            for rec in recordings:
                rec_artist = get_mb_artist_name(rec)
                rec_title = rec.get("title", "")
                sa, st = _score_pair(rec_artist, rec_title, artist, title)
                
                # Minimum threshold match score (e.g. sa>=3 and st>=3)
                if sa >= 3 and st >= 3:
                    years = []
                    for rel in rec.get("releases", []):
                        date = rel.get("date", "")
                        if date and len(date) >= 4:
                            y = date[:4]
                            if y.isdigit() and 1960 <= int(y) <= 2026:
                                years.append(int(y))
                    if years:
                        min_yr = str(min(years))
                        score = sa + st
                        if score > best_score:
                            best_score = score
                            best_year = min_yr
                        elif score == best_score:
                            if best_year == "N/A" or int(min_yr) < int(best_year):
                                best_year = min_yr
            
            # If we found a good match, we can stop querying other fallbacks
            if best_year != "N/A":
                print(f"      [MB MATCH] {query} -> Found year {best_year} with score {best_score}")
                return best_year

        except Exception as e:
            print(f"  Errore MusicBrainz per {query}: {e}")

    return best_year

test_songs = [
    "FEDERICA ABBATE - SUPERMAN",
    "ANNALISA - L'Ultimo Addio",
    "TIZIANO FERRO FEAT. LAZZA - XXDONO",
    "MARCO MENGONI - Dove Si Vola",
    "MR RAIN - LUNEDI' NERO"
]

for s in test_songs:
    print(f"\nSong: {s}")
    yr = get_year_from_musicbrainz_scored(s)
    print(f"Result: {yr}")
