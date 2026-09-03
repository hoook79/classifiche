import requests
from bs4 import BeautifulSoup

url = "https://myradioonline.it/radio-italia/playlist"
headers = {'User-Agent': 'Mozilla/5.0'}
r = requests.get(url, headers=headers)
soup = BeautifulSoup(r.text, 'html.parser')
rows = soup.select('.js-songListC .yt-row')

if rows:
    print("Full HTML of Radio Italia Row 2:")
    print(rows[1].prettify())
