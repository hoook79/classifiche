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
    'SOCS': 'CAESHAgBEhJnd2NfMjAyNDA4MTktUkNfMF8xGgJpdCABIContent'
}

session = requests.Session()
r1 = session.get(url, headers=headers, cookies=cookies, timeout=10)

print(f"Page 1: status={r1.status_code}, length={len(r1.text)}")

soup1 = BeautifulSoup(r1.text, 'html.parser')

# IGNORIAMO il meta refresh e cerchiamo il tag <a> che inizia con `/search?q=`
real_url = None
for a in soup1.find_all('a', href=True):
    href = a['href']
    if href.startswith('/search?'):
        real_url = href
        break

if real_url:
    if real_url.startswith('/'):
        real_url = "https://www.google.com" + real_url
        
    print(f"Real URL found (from link): {real_url}")
    
    # Facciamo la richiesta al vero URL dei risultati!
    r2 = session.get(real_url, headers=headers, cookies=cookies, timeout=10)
    print(f"Page 2: status={r2.status_code}, length={len(r2.text)}")
    
    soup2 = BeautifulSoup(r2.text, 'html.parser')
    
    # Cerchiamo tutti i link esterni che contengono "earone"
    external_links = []
    for a in soup2.find_all('a', href=True):
        href = a['href']
        if 'earone' in href and not href.startswith('/search'):
            external_links.append(href)
        elif href.startswith('/url?q='):
            parsed = urllib.parse.urlparse(href)
            query_params = urllib.parse.parse_qs(parsed.query)
            if 'q' in query_params:
                actual_url = query_params['q'][0]
                if 'earone' in actual_url:
                    external_links.append(actual_url)
                    
    print(f"\nFound {len(external_links)} earone links:")
    for l in external_links:
        print(f"  -> {l}")
        
    if not external_links:
        print("\n--- BODY TEXT OF RESULTS PAGE ---")
        print(soup2.get_text()[:2000])
else:
    print("Could not find any redirect URL in <a> tags!")
