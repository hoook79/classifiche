import requests
from bs4 import BeautifulSoup
import urllib.parse
import sys
import base64
import re

sys.stdout.reconfigure(encoding='utf-8')

query = "MARCO MASINI E poi ti ho visto cadere earone"
url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}"
headers = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1'
}

r = requests.get(url, headers=headers, timeout=10)
soup = BeautifulSoup(r.text, 'html.parser')

print("ALL DECODED EXTERNAL LINKS FROM BING:")
count = 0
for a in soup.find_all('a', href=True):
    href = a['href']
    
    # Se il link è un click tracking di Bing (es. /ck/a?...)
    if '/ck/a?' in href:
        parsed = urllib.parse.urlparse(href)
        query_params = urllib.parse.parse_qs(parsed.query)
        if 'u' in query_params:
            u_val = query_params['u'][0]
            # Gli URL di Bing iniziano solitamente con "a1" seguito dal base64 dell'URL
            if u_val.startswith('a1'):
                base64_str = u_val[2:]
                # Aggiunge padding se necessario per base64
                padding = len(base64_str) % 4
                if padding > 0:
                    base64_str += '=' * (4 - padding)
                try:
                    # Rimuoviamo eventuali caratteri speciali o proviamo a decodificare
                    decoded_bytes = base64.b64decode(base64_str.encode('utf-8'), validate=False)
                    decoded_url = decoded_bytes.decode('utf-8', errors='ignore')
                    
                    if 'earone' in decoded_url:
                        print(f"  DECODED LINK: {decoded_url} | Text: {a.get_text().strip()}")
                        count += 1
                except Exception as e:
                    pass
    elif 'earone' in href and not href.startswith('/'):
        print(f"  DIRECT LINK: {href} | Text: {a.get_text().strip()}")
        count += 1

if count == 0:
    print("No external earone links decoded.")
    # Stampiamo i primi 30 link generici
    print("\nFIRST 30 GENERIC LINKS:")
    for a in soup.find_all('a', href=True)[:30]:
        print(f"  Href: {a['href']} | Text: {a.get_text().strip()[:50]}")
