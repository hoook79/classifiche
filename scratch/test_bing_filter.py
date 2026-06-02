import requests
from bs4 import BeautifulSoup
import urllib.parse
import sys

sys.stdout.reconfigure(encoding='utf-8')

query = "MARCO MASINI E poi ti ho visto cadere earone"
url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}"
headers = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1'
}

r = requests.get(url, headers=headers, timeout=10)
soup = BeautifulSoup(r.text, 'html.parser')

print("EXTERNAL EARONE LINKS FROM BING:")
for a in soup.find_all('a', href=True):
    href = a['href']
    if 'earone.it' in href or 'earone.com' in href:
        print(f"  Href: {href} | Text: {a.get_text().strip()}")
