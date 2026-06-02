import requests
from bs4 import BeautifulSoup
import urllib.parse
import sys

sys.stdout.reconfigure(encoding='utf-8')

query = "MARCO MASINI E poi ti ho visto cadere earone"
url = f"https://search.yahoo.com/search?p={urllib.parse.quote(query)}"
headers = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9'
}

r = requests.get(url, headers=headers, timeout=10)
print(f"Yahoo Mobile: status={r.status_code}, length={len(r.text)}")

soup = BeautifulSoup(r.text, 'html.parser')
links = []
for a in soup.find_all('a', href=True):
    href = a['href']
    
    # Se il link è un redirect di Yahoo
    if '/RU=' in href:
        parsed = urllib.parse.urlparse(href)
        query_params = urllib.parse.parse_qs(parsed.query)
        # O estraiamo RU con regex
        match = re.search(r'/RU=([^/]+)', href)
        if match:
            decoded_url = urllib.parse.unquote(match.group(1))
            if 'earone' in decoded_url:
                links.append((decoded_url, a.get_text().strip()))
        else:
            # Proviamo a decodificare l'intero URL se contiene RU
            try:
                # Trova RU=... fino alla fine o a un separatore /
                ru_part = href.split('/RU=')[1].split('/')[0]
                decoded_url = urllib.parse.unquote(ru_part)
                if 'earone' in decoded_url:
                    links.append((decoded_url, a.get_text().strip()))
            except:
                pass
    elif 'earone' in href and not href.startswith('/'):
        links.append((href, a.get_text().strip()))

# Aggiungiamo regex per estrarre RU in modo semplice
import re
print(f"Found {len(links)} earone links:")
for l, text in links:
    print(f"  Link: {l} | Text: {text}")
