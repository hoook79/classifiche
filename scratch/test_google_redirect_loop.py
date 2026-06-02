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

session = requests.Session()
session.headers.update(headers)
session.cookies.set('SOCS', 'CAESHAgBEhJnd2NfMjAyNDA4MTktUkNfMF8xGgJpdCABIContent', domain='.google.com')

curr_url = url
for loop in range(1, 6):
    r = session.get(curr_url, timeout=10)
    print(f"Loop {loop}: status={r.status_code}, length={len(r.text)}, URL={curr_url[:100]}")
    
    soup = BeautifulSoup(r.text, 'html.parser')
    
    # Cerchiamo se ci sono i veri risultati della ricerca
    external_links = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith('/url?q='):
            parsed = urllib.parse.urlparse(href)
            query_params = urllib.parse.parse_qs(parsed.query)
            if 'q' in query_params:
                actual_url = query_params['q'][0]
                if 'earone' in actual_url:
                    external_links.append(actual_url)
        elif 'earone' in href and not href.startswith('/search'):
            external_links.append(href)
            
    if external_links:
        print(f"\nSUCCESS! Found {len(external_links)} earone links:")
        for l in external_links:
            print(f"  -> {l}")
        break
        
    # Cerca il prossimo redirect link
    redirect_link = None
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith('/search?'):
            redirect_link = href
            break
            
    if not redirect_link:
        print("No redirect link found. Stopping.")
        print(soup.get_text()[:1000])
        break
        
    curr_url = "https://www.google.com" + redirect_link
