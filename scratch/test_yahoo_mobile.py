import requests
from bs4 import BeautifulSoup
import urllib.parse
import sys

sys.stdout.reconfigure(encoding='utf-8')

query = "ANNALISA Sinceramente earone"
url = f"https://search.yahoo.com/search?p={urllib.parse.quote(query)}"
headers = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9'
}

try:
    r = requests.get(url, headers=headers, timeout=10)
    print(f"Yahoo Mobile: status={r.status_code}, length={len(r.text)}")
    
    soup = BeautifulSoup(r.text, 'html.parser')
    links = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        if 'earone' in href:
            links.append(href)
            
    print(f"Found {len(links)} earone links:")
    for l in links[:10]:
        print(f"  {l}")
        
    if not links:
        print("\nFIRST 20 GENERIC EXTERNAL LINKS:")
        for a in soup.find_all('a', href=True)[:20]:
            href = a['href']
            if href.startswith('http') and 'yahoo.com' not in href:
                print(f"  Href: {href} | Text: {a.get_text().strip()[:50]}")
except Exception as e:
    print(f"Yahoo Mobile error: {e}")
