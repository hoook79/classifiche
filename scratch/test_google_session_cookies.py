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

# Usiamo una sessione e inseriamo i cookie iniziali nella sessione
session = requests.Session()
session.headers.update(headers)
session.cookies.set('SOCS', 'CAESHAgBEhJnd2NfMjAyNDA4MTktUkNfMF8xGgJpdCABIContent', domain='.google.com')

# Prima richiesta (ottiene la pagina di redirect ed i cookie NID, 1P_JAR, ecc.)
r1 = session.get(url, timeout=10)
print(f"Page 1: status={r1.status_code}, length={len(r1.text)}")
print(f"Cookies in session after Page 1: {session.cookies.get_dict()}")

soup1 = BeautifulSoup(r1.text, 'html.parser')

redirect_link = None
for a in soup1.find_all('a', href=True):
    href = a['href']
    if href.startswith('/search?'):
        redirect_link = href
        break

if redirect_link:
    real_url = "https://www.google.com" + redirect_link
    print(f"Following redirect: {real_url}")
    
    # Seconda richiesta (usando la sessione e mantenendo i cookie impostati da Google!)
    r2 = session.get(real_url, timeout=10)
    print(f"Page 2: status={r2.status_code}, length={len(r2.text)}")
    print(f"Cookies in session after Page 2: {session.cookies.get_dict()}")
    
    soup2 = BeautifulSoup(r2.text, 'html.parser')
    
    external_links = []
    for a in soup2.find_all('a', href=True):
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
            
    print(f"\nFound {len(external_links)} earone links:")
    for l in external_links:
        print(f"  -> {l}")
        
    if not external_links:
        print("\n--- BODY TEXT OF RESULTS PAGE ---")
        print(soup2.get_text()[:2000])
else:
    print("Could not find any redirect URL in <a> tags!")
