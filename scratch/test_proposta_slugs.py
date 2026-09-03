import requests
from bs4 import BeautifulSoup

slugs = [
    'radiopropostainblu',
    'propostainblu',
    'propostaaosta',
    'proposta',
    'radioproposta',
    'radiopropostaaosta',
    'inblu',
    'radioinbluaosta',
    'proposta-aosta'
]

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

for slug in slugs:
    url = f"https://onlineradiobox.com/it/{slug}/playlist/"
    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        rows = soup.select('table.tablelist-schedule tr')
        print(f"Slug: {slug} | Status: {r.status_code} | Tracks: {len(rows)}")
        if len(rows) > 0:
            print(f"  Example: {rows[0].get_text(strip=True)[:100]}")
    except Exception as e:
        print(f"Error {slug}: {e}")
