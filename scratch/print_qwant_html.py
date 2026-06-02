import requests
from bs4 import BeautifulSoup
import urllib.parse
import sys

sys.stdout.reconfigure(encoding='utf-8')

query = "MARCO MASINI E poi ti ho visto cadere earone"
url_qwant = f"https://www.qwant.com/?q={urllib.parse.quote(query)}&t=web"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

r = requests.get(url_qwant, headers=headers, timeout=10)
print(f"Qwant status={r.status_code}, length={len(r.text)}")

soup = BeautifulSoup(r.text, 'html.parser')
print(f"Contains 'earone': {'earone' in r.text or 'EARONE' in r.text}")
print(f"Contains 'Masini': {'Masini' in r.text or 'MASINI' in r.text}")

print("\nALL LINKS IN QWANT:")
count = 0
for a in soup.find_all('a', href=True):
    href = a['href']
    text = a.get_text().strip()
    if href.startswith('http') or len(text) > 5:
        print(f"  Href: {href} | Text: {text[:50]}")
        count += 1
        if count >= 30:
            break
