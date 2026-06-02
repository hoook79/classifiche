import requests
from bs4 import BeautifulSoup
import urllib.parse
import sys

# Forza encoding in UTF-8
sys.stdout.reconfigure(encoding='utf-8')

query = "MARCO MASINI E poi ti ho visto cadere earone"
url = f"https://www.ask.com/web?q={urllib.parse.quote(query)}"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

r = requests.get(url, headers=headers, timeout=10)
print(f"Ask.com status={r.status_code}, length={len(r.text)}")

soup = BeautifulSoup(r.text, 'html.parser')
results = soup.find_all(class_='PartialSearchResults-item')
print(f"Found {len(results)} search results")
for i, res in enumerate(results[:5]):
    print(f"\n--- RESULT {i+1} ---")
    print(res.get_text()[:300])
    link = res.find('a')
    if link:
        print(f"Link: {link.get('href')}")

if not results:
    print("\n--- FIRST 1000 CHARS of text ---")
    print(soup.get_text()[:1000])
