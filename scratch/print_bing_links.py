import requests
from bs4 import BeautifulSoup
import urllib.parse

query = "ANNALISA Sinceramente earone"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

url_bing = f"https://www.bing.com/search?q={urllib.parse.quote(query)}"
r = requests.get(url_bing, headers=headers, timeout=10)
soup = BeautifulSoup(r.text, 'html.parser')

print("ALL EXTERNAL LINKS IN BING:")
for a in soup.find_all('a', href=True):
    href = a['href']
    if href.startswith('http') and 'bing.com' not in href:
        print(f"  {href}")
