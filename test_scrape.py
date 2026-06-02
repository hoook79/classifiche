import requests
from bs4 import BeautifulSoup
import re

url = "https://onlineradiobox.com/it/divina/playlist/"
r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
soup = BeautifulSoup(r.text, 'html.parser')
links = soup.find_all('a', href=True)
for a in links:
    if 'playlist' in a['href']:
        print(f"Text: {a.get_text(strip=True)} | Href: {a['href']}")
