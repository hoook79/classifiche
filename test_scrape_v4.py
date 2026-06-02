import requests
from bs4 import BeautifulSoup
import re

def check_date(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, 'html.parser')
    day_el = soup.select_one('.menuitem_selected, .menuitem_active')
    if day_el:
        text = day_el.get_text(strip=True)
        print(f"URL: {url} | Selected Day Text: {text}")
        match = re.search(r'(\d{2}\.\d{2})', text)
        if match:
            print(f"  Extracted Date: {match.group(1)}")
    else:
        print(f"URL: {url} | No selected day element found")

check_date("https://onlineradiobox.com/it/divina/playlist/")
check_date("https://onlineradiobox.com/it/divina/playlist/1")
check_date("https://onlineradiobox.com/it/divina/playlist/2")
