import requests
from bs4 import BeautifulSoup
import urllib.parse
import sys

sys.stdout.reconfigure(encoding='utf-8')

query = "MARCO MASINI E poi ti ho visto cadere earone"
encoded_query = urllib.parse.quote(query)
url = f"https://www.google.com/search?q={encoded_query}&gbv=1"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

cookies = {
    'SOCS': 'CAESHAgBEhJnd2NfMjAyNDA4MTktUkNfMF8xGgJpdCABIContent',
    'CONSENT': 'YES+cb.20210328-17-p0.it+FX+999'
}

r = requests.get(url, headers=headers, cookies=cookies, timeout=10)
print(f"Google status={r.status_code}, length={len(r.text)}")

soup = BeautifulSoup(r.text, 'html.parser')
links = []
for a in soup.find_all('a', href=True):
    href = a['href']
    if 'earone' in href or '/url?q=' in href:
        links.append(href)

print(f"Found {len(links)} links:")
for l in links[:20]:
    if 'earone' in l:
        print(f"  EARONE LINK: {l}")
    else:
        if '/url?q=' in l:
            parsed = urllib.parse.urlparse(l)
            query_params = urllib.parse.parse_qs(parsed.query)
            if 'q' in query_params:
                actual_url = query_params['q'][0]
                if 'earone' in actual_url:
                    print(f"  EARONE LINK (decoded): {actual_url}")
                    
if not links:
    print(r.text[:2000])
