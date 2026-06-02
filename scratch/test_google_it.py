import requests
from bs4 import BeautifulSoup
import urllib.parse
import sys

sys.stdout.reconfigure(encoding='utf-8')

query = "MARCO MASINI E poi ti ho visto cadere earone"
encoded_query = urllib.parse.quote(query)
url = f"https://www.google.it/search?q={encoded_query}"

headers = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1'
}

cookies = {
    'SOCS': 'CAESHAgBEhJnd2NfMjAyNDA4MTktUkNfMF8xGgJpdCABIContent',
    'CONSENT': 'YES+cb.20210328-17-p0.it+FX+999'
}

r = requests.get(url, headers=headers, cookies=cookies, timeout=10)
print(f"Google IT Mobile: status={r.status_code}, length={len(r.text)}")

soup = BeautifulSoup(r.text, 'html.parser')
links = []
for a in soup.find_all('a', href=True):
    href = a['href']
    if 'earone' in href:
        links.append(href)
    elif '/url?q=' in href:
        parsed = urllib.parse.urlparse(href)
        query_params = urllib.parse.parse_qs(parsed.query)
        if 'q' in query_params:
            actual_url = query_params['q'][0]
            if 'earone' in actual_url:
                links.append(actual_url)

print(f"Found {len(links)} earone links:")
for l in links[:10]:
    print(f"  {l}")

if not links:
    print("\nFIRST 1000 CHARS OF BODY:")
    print(soup.get_text()[:1000])
