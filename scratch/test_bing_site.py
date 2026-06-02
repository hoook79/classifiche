import requests
from bs4 import BeautifulSoup
import urllib.parse
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Proviamo sia site:earone.it che site:earone.com
queries = [
    "MARCO MASINI E poi ti ho visto cadere site:earone.it",
    "MARCO MASINI E poi ti ho visto cadere site:earone.com",
    "ANNALISA Sinceramente site:earone.it"
]

headers = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1'
}

for q in queries:
    print(f"\nQuerying Bing for: '{q}'")
    url = f"https://www.bing.com/search?q={urllib.parse.quote(q)}"
    
    r = requests.get(url, headers=headers, timeout=10)
    print(f"Bing: status={r.status_code}, length={len(r.text)}")
    
    soup = BeautifulSoup(r.text, 'html.parser')
    
    external_links = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith('http') and 'bing.com' not in href:
            if 'earone.it' in href or 'earone.com' in href:
                external_links.append(href)
                
    print(f"Found {len(external_links)} earone links:")
    for l in external_links:
        print(f"  -> {l}")
