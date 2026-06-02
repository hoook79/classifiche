import requests
from bs4 import BeautifulSoup
import urllib.parse
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

query = "MARCO MASINI E poi ti ho visto cadere earone"
url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}"

# Usiamo un User-Agent diverso, ad esempio Firefox o un mobile user agent
headers = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1'
}

r = requests.get(url, headers=headers, timeout=10)
print(f"Bing status={r.status_code}, length={len(r.text)}")

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
    print("\nFIRST 1000 CHARS OF BODY:")
    print(soup.get_text()[:1000])
