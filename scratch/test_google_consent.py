import requests
from bs4 import BeautifulSoup
import urllib.parse

query = "ANNALISA Sinceramente earone"
encoded_query = urllib.parse.quote(query)

url_google = f"https://www.google.com/search?q={encoded_query}"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# Impostiamo il cookie SOCS che dice a Google che le preferenze dei cookie sono state accettate (formato standard GDPR bypass)
cookies = {
    'SOCS': 'CAESHAgBEhJnd2NfMjAyNDA4MTktUkNfMF8xGgJpdCABIContent'
}

r = requests.get(url_google, headers=headers, cookies=cookies, timeout=10)
print(f"Google status={r.status_code}, length={len(r.text)}")

soup = BeautifulSoup(r.text, 'html.parser')
links = []
for a in soup.find_all('a', href=True):
    href = a['href']
    if 'earone' in href:
        links.append(href)

print(f"Found {len(links)} earone links:")
for l in links[:5]:
    print(f"  {l}")
