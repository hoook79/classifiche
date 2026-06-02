import requests
from bs4 import BeautifulSoup
import urllib.parse
import sys

sys.stdout.reconfigure(encoding='utf-8')

query = "MARCO MASINI E poi ti ho visto cadere earone"
url = f"https://swisscows.com/web?query={urllib.parse.quote(query)}"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

r = requests.get(url, headers=headers, timeout=10)
soup = BeautifulSoup(r.text, 'html.parser')

print("ALL LINKS IN SWISSCOWS:")
for a in soup.find_all('a', href=True):
    href = a['href']
    text = a.get_text().strip()
    if href.startswith('http') or len(text) > 5:
        print(f"  Link: {href} | Text: {text[:100]}")
