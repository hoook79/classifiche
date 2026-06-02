import requests
from bs4 import BeautifulSoup
import urllib.parse
import sys
import re
import time

sys.stdout.reconfigure(encoding='utf-8')

def test_search(query):
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7'
    }
    
    # 1. Prova Yahoo
    url_yahoo = f"https://search.yahoo.com/search?p={urllib.parse.quote(query)}"
    print(f"Querying Yahoo: {url_yahoo}...")
    try:
        r = requests.get(url_yahoo, headers=headers, timeout=10)
        print(f"Yahoo response: status={r.status_code}, length={len(r.text)}")
        if r.status_code == 200 and len(r.text) > 5000:
            soup = BeautifulSoup(r.text, 'html.parser')
            for a in soup.find_all('a', href=True):
                href = a['href']
                if '/RU=' in href:
                    match = re.search(r'/RU=([^/]+)', href)
                    if match:
                        href = urllib.parse.unquote(match.group(1))
                if 'earone' in href:
                    print(f"  YAHOO FOUND EARONE LINK: {href}")
    except Exception as e:
        print(f"Yahoo error: {e}")
        
    print("\nWaiting 5 seconds to avoid rate limiting...")
    time.sleep(5)
    
    # 2. Prova Bing
    url_bing = f"https://www.bing.com/search?q={urllib.parse.quote(query)}"
    print(f"\nQuerying Bing: {url_bing}...")
    try:
        r = requests.get(url_bing, headers=headers, timeout=10)
        print(f"Bing response: status={r.status_code}, length={len(r.text)}")
        if r.status_code == 200 and len(r.text) > 5000:
            soup = BeautifulSoup(r.text, 'html.parser')
            for a in soup.find_all('a', href=True):
                href = a['href']
                if 'earone' in href and not href.startswith('/'):
                    print(f"  BING FOUND EARONE LINK: {href}")
    except Exception as e:
        print(f"Bing error: {e}")

test_search("MARCO MASINI E poi ti ho visto cadere earone")
