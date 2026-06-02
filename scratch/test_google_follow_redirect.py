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

# Primo step: ottiene la pagina di reindirizzamento
session = requests.Session()
r1 = session.get(url, headers=headers, cookies=cookies, timeout=10)
soup1 = BeautifulSoup(r1.text, 'html.parser')

redirect_link = None
for a in soup1.find_all('a', href=True):
    href = a['href']
    if href.startswith('/search?q='):
        redirect_link = href
        break

if redirect_link:
    print(f"Following redirect: https://www.google.com{redirect_link}")
    r2 = session.get(f"https://www.google.com{redirect_link}", headers=headers, cookies=cookies, timeout=10)
    print(f"Google Real Results: status={r2.status_code}, length={len(r2.text)}")
    
    soup2 = BeautifulSoup(r2.text, 'html.parser')
    
    # Cerchiamo tutti i link esterni che contengono "earone"
    links = []
    for a in soup2.find_all('a', href=True):
        href = a['href']
        if 'earone' in href:
            links.append(href)
        elif '/url?q=' in href:
            parsed = urllib.parse.urlparse(href)
            query_params = urllib.parse.parse_qs(parsed.query)
            if 'q' in query_params:
                actual_url = query_params['q'][0]
                if 'earone' in actual_url:
                    links.append(actual_url)
                    
    print(f"Found {len(links)} earone links:")
    for l in links[:5]:
        print(f"  {l}")
        
    if not links:
        print("\n--- BODY TEXT OF RESULTS PAGE ---")
        print(soup2.get_text()[:2000])
else:
    print("No redirect link found!")
