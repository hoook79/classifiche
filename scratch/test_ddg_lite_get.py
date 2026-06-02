import requests
from bs4 import BeautifulSoup
import urllib.parse

query = "MARCO MASINI E poi ti ho visto cadere earone"
url = f"https://lite.duckduckgo.com/lite/?q={urllib.parse.quote(query)}"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

r = requests.get(url, headers=headers, timeout=10)
print(f"DDG Lite GET: status={r.status_code}, length={len(r.text)}")

soup = BeautifulSoup(r.text, 'html.parser')
links = []
for a in soup.find_all('a', href=True):
    href = a['href']
    if 'earone' in href:
        links.append(href)

print(f"Found {len(links)} earone links:")
for l in links[:5]:
    print(f"  {l}")

# Stampiamo tutti i link esterni per sicurezza
print("\nALL EXTERNAL LINKS:")
for a in soup.find_all('a', href=True):
    href = a['href']
    if href.startswith('http') and 'duckduckgo' not in href:
        print(f"  {href}")
