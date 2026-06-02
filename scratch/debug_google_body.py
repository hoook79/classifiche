import requests
from bs4 import BeautifulSoup
import urllib.parse
import sys

sys.stdout.reconfigure(encoding='utf-8')

query = "MARCO MASINI E poi ti ho visto cadere earone"
encoded_query = urllib.parse.quote(query)
url = f"https://www.google.com/search?q={encoded_query}&gbv=1"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

cookies = {
    'SOCS': 'CAESHAgBEhJnd2NfMjAyNDA4MTktUkNfMF8xGgJpdCABIContent',
    'CONSENT': 'YES+cb.20210328-17-p0.it+FX+999'
}

r = requests.get(url, headers=headers, cookies=cookies, timeout=10)
soup = BeautifulSoup(r.text, 'html.parser')

print(f"Page text contains 'Prima di procedere': {'Prima di procedere' in r.text}")
print(f"Page text contains 'Before you continue': {'Before you continue' in r.text}")
print(f"Page text contains 'Masini': {'Masini' in r.text or 'MASINI' in r.text}")
print(f"Page text contains 'cadere': {'cadere' in r.text or 'CADERE' in r.text}")

print("\n--- BODY TEXT SNIPPET ---")
body = soup.find('body')
if body:
    print(body.get_text()[:1500])
