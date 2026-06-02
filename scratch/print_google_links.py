import requests
from bs4 import BeautifulSoup
import urllib.parse

query = "ANNALISA Sinceramente earone"
encoded_query = urllib.parse.quote(query)

url_google = f"https://www.google.com/search?q={encoded_query}"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

cookies = {
    'SOCS': 'CAESHAgBEhJnd2NfMjAyNDA4MTktUkNfMF8xGgJpdCABIContent'
}

r = requests.get(url_google, headers=headers, cookies=cookies, timeout=10)
soup = BeautifulSoup(r.text, 'html.parser')

print("ALL EXTERNAL OR REDIRECT LINKS ON GOOGLE:")
for a in soup.find_all('a', href=True):
    href = a['href']
    if 'earone' in href or '/url?' in href or href.startswith('http'):
        if 'google' not in href or '/url?' in href:
            print(f"  {href}")
