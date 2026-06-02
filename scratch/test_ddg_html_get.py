import requests
from bs4 import BeautifulSoup
import urllib.parse
import sys

sys.stdout.reconfigure(encoding='utf-8')

query = "MARCO MASINI E poi ti ho visto cadere earone"
url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'it-IT,it;q=0.8,en-US;q=0.5,en;q=0.3',
    'Referer': 'https://duckduckgo.com/'
}

r = requests.get(url, headers=headers, timeout=10)
print(f"DDG HTML status={r.status_code}, length={len(r.text)}")

soup = BeautifulSoup(r.text, 'html.parser')
links = []
for a in soup.find_all('a', class_='result__snippet', href=True):
    href = a['href']
    links.append(href)
    
if not links:
    # Cerchiamo tutti i link esterni generici
    for a in soup.find_all('a', href=True):
        href = a['href']
        if 'earone' in href:
            links.append(href)

print(f"Found {len(links)} links:")
for l in links[:10]:
    print(f"  {l}")

if not links:
    print("\nFIRST 1000 CHARS:")
    print(soup.get_text()[:1000])
