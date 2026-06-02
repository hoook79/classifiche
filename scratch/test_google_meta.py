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
r = session.get(url, headers=headers, cookies=cookies, timeout=10)

print(f"Initial Page: status={r.status_code}, length={len(r.text)}")

soup = BeautifulSoup(r.text, 'html.parser')

# Cerchiamo il meta refresh tag
meta_refresh = soup.find('meta', attrs={'http-equiv': 'refresh'})
real_url = None
if meta_refresh:
    content = meta_refresh.get('content', '')
    if 'url=' in content.lower():
        parts = content.split('url=')
        if len(parts) > 1:
            real_url = parts[1]

# Se non c'è il meta refresh, cerchiamo il primo link `/search?`
if not real_url:
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith('/search?'):
            real_url = href
            break

if real_url:
    # Assicuriamoci che sia un URL assoluto
    if real_url.startswith('/'):
        real_url = "https://www.google.com" + real_url
        
    print(f"Real URL found: {real_url}")
    
    # Facciamo la richiesta al vero URL dei risultati!
    r_results = session.get(real_url, headers=headers, cookies=cookies, timeout=10)
    print(f"Results Page: status={r_results.status_code}, length={len(r_results.text)}")
    
    soup_res = BeautifulSoup(r_results.text, 'html.parser')
    
    # Cerchiamo tutti i link esterni nella vera pagina dei risultati!
    external_links = []
    for a in soup_res.find_all('a', href=True):
        href = a['href']
        # Google racchiude i link in `/url?q=...` nella versione gbv=1
        if href.startswith('/url?q='):
            parsed = urllib.parse.urlparse(href)
            query_params = urllib.parse.parse_qs(parsed.query)
            if 'q' in query_params:
                actual_url = query_params['q'][0]
                if 'earone' in actual_url:
                    external_links.append(actual_url)
        elif 'earone' in href and not href.startswith('/search'):
            external_links.append(href)
            
    print(f"\nFound {len(external_links)} earone links:")
    for l in external_links:
        print(f"  -> {l}")
        
    if not external_links:
        print("\n--- BODY TEXT OF RESULTS PAGE ---")
        print(soup_res.get_text()[:2000])
else:
    print("Could not find any redirect URL!")
