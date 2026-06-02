import requests
from bs4 import BeautifulSoup
import urllib.parse
import sys

sys.stdout.reconfigure(encoding='utf-8')

query = "ANNALISA Sinceramente earone"
url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}"
headers = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1'
}

r = requests.get(url, headers=headers, timeout=10)
print(f"Bing status={r.status_code}, length={len(r.text)}")

soup = BeautifulSoup(r.text, 'html.parser')
links = []
for a in soup.find_all('a', href=True):
    href = a['href']
    if 'earone' in href and not href.startswith('/'):
        links.append((href, a.get_text().strip()))
    elif '/ck/a?' in href:
        parsed = urllib.parse.urlparse(href)
        query_params = urllib.parse.parse_qs(parsed.query)
        if 'u' in query_params:
            u_val = query_params['u'][0]
            if u_val.startswith('a1'):
                import base64
                base64_str = u_val[2:]
                padding = len(base64_str) % 4
                if padding > 0:
                    base64_str += '=' * (4 - padding)
                try:
                    decoded = base64.b64decode(base64_str.encode('utf-8'), validate=False).decode('utf-8', errors='ignore')
                    if 'earone' in decoded:
                        links.append((decoded, a.get_text().strip()))
                except:
                    pass

print(f"Found {len(links)} earone links:")
for l, text in links:
    print(f"  Link: {l} | Text: {text}")
