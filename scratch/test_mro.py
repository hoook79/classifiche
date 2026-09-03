import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

def test_mro(slug, label):
    url = f"https://myradioonline.it/{slug}/playlist"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    # We simulate a POST request for today's date
    date_str = datetime.now().strftime("%d-%m-%Y")
    data = {
        'from': date_str,
        'to': date_str
    }
    
    try:
        r = requests.post(url, headers=headers, data=data, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        rows = soup.select('.js-songListC .yt-row')
        print(f"MRO {label} ({slug}): Status {r.status_code}, Found {len(rows)} tracks")
        if len(rows) > 0:
            artist_el = rows[0].select_one('[itemprop="byArtist"]')
            title_el = rows[0].select_one('[itemprop="name"]')
            time_el = rows[0].select_one('.txt2.mcolumn')
            print(f"  Example track: {time_el.get_text(strip=True) if time_el else ''} - {artist_el.get_text(strip=True) if artist_el else ''} - {title_el.get_text(strip=True) if title_el else ''}")
    except Exception as e:
        print(f"Error MRO {label}: {e}")

if __name__ == "__main__":
    test_mro('radio-birikina', 'Birikina')
    test_mro('radio-bruno', 'Bruno')
    test_mro('radio-kiss-kiss', 'Kiss Kiss')
    test_mro('m2o', 'm2o')
