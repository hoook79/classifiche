import requests
from bs4 import BeautifulSoup
import urllib.parse
import sys

sys.stdout.reconfigure(encoding='utf-8')

q = "ANNALISA Sinceramente site:earone.it"
url = f"https://www.bing.com/search?q={urllib.parse.quote(q)}"
headers = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1'
}

r = requests.get(url, headers=headers, timeout=10)
soup = BeautifulSoup(r.text, 'html.parser')

print("ALL EXTERNAL LINKS FOR SITE:EARONE.IT IN BING:")
count = 0
for a in soup.find_all('a', href=True):
    href = a['href']
    if href.startswith('http') and 'bing.com' not in href:
        print(f"  Href: {href} | Text: {a.get_text().strip()[:50]}")
        count += 1
        
if count == 0:
    print("No external links found. Let's see first 1000 chars of body:")
    print(soup.get_text()[:1000])
