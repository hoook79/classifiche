import requests
from bs4 import BeautifulSoup
import re

url = "https://radiocrt.it/playlist-calabria/"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
r = requests.get(url, headers=headers)
soup = BeautifulSoup(r.text, 'html.parser')

print("--- Scanning all data-prsidekick- elements ---")
for tag in soup.find_all(attrs=True):
    for attr in tag.attrs:
        if attr.startswith('data-prsidekick-'):
            print(f"Tag: {tag.name}, class: {tag.get('class')}")
            print(f"Attribute: {attr} = {tag[attr]}")
            print()
