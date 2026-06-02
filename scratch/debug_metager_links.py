import requests
from bs4 import BeautifulSoup
import urllib.parse
import sys

sys.stdout.reconfigure(encoding='utf-8')

query = "MARCO MASINI E poi ti ho visto cadere earone"
url = f"https://metager.org/meta/meta.ger3?eingabe={urllib.parse.quote(query)}"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

r = requests.get(url, headers=headers, timeout=10)
soup = BeautifulSoup(r.text, 'html.parser')

print(f"Metager length: {len(r.text)}")
print("FIRST 100 LINKS IN METAGER:")
count = 0
for a in soup.find_all('a', href=True):
    href = a['href']
    text = a.get_text().strip()
    print(f"  Href: {href} | Text: {text[:50]}")
    count += 1
    if count >= 100:
        break
        
if count == 0:
    print("\nNo links found. Body snippet:")
    print(soup.get_text()[:2000])
