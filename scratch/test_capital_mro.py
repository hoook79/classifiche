import requests
from bs4 import BeautifulSoup

slugs = ['radio-capital', 'capital']
headers = {'User-Agent': 'Mozilla/5.0'}

for slug in slugs:
    url = f"https://myradioonline.it/{slug}/playlist"
    print(f"Testing MyRadioOnline URL: {url}")
    try:
        # Use POST date format as used by other scrapers or just GET
        # First, try GET to see if the page exists
        r = requests.get(url, headers=headers, timeout=10)
        print(f"  GET Status Code: {r.status_code}")
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            rows = soup.select('.js-songListC .yt-row')
            print(f"  GET: Trovate {len(rows)} righe.")
            
            # Also try POST for today's date
            from datetime import datetime
            today_str = datetime.now().strftime("%d-%m-%Y")
            data = {'from': today_str, 'to': today_str}
            r_post = requests.post(url, data=data, headers=headers, timeout=10)
            soup_post = BeautifulSoup(r_post.text, 'html.parser')
            rows_post = soup_post.select('.js-songListC .yt-row')
            print(f"  POST (today): Trovate {len(rows_post)} righe.")
            for i, row in enumerate(rows_post[:3]):
                artist_el = row.select_one('[itemprop="byArtist"]')
                title_el = row.select_one('[itemprop="name"]')
                time_el = row.select_one('.txt2.mcolumn')
                art_txt = artist_el.get_text(strip=True) if artist_el else "None"
                tit_txt = title_el.get_text(strip=True) if title_el else "None"
                tim_txt = time_el.get_text(strip=True) if time_el else "None"
                print(f"    {tim_txt}: {art_txt} - {tit_txt}")
    except Exception as e:
        print(f"  Errore: {e}")
