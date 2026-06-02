import requests
from bs4 import BeautifulSoup
import urllib.parse
import sys
import base64

sys.stdout.reconfigure(encoding='utf-8')

query = "ANNALISA Sinceramente earone"
url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}"
headers = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1'
}

r = requests.get(url, headers=headers, timeout=10)
soup = BeautifulSoup(r.text, 'html.parser')

print("ALL DECODED EXTERNAL BING LINKS:")
for a in soup.find_all('a', href=True):
    href = a['href']
    if '/ck/a?' in href:
        parsed = urllib.parse.urlparse(href)
        query_params = urllib.parse.parse_qs(parsed.query)
        if 'u' in query_params:
            u_val = query_params['u'][0]
            if u_val.startswith('a1'):
                base64_str = u_val[2:]
            else:
                base64_str = u_val
                
            padding = len(base64_str) % 4
            if padding > 0:
                base64_str += '=' * (4 - padding)
            try:
                decoded = base64.b64decode(base64_str.encode('utf-8'), validate=False).decode('utf-8', errors='ignore')
                print(f"  Decoded: {decoded} | Text: {a.get_text().strip()[:50]}")
            except Exception as e:
                pass
    elif href.startswith('http') and 'bing.com' not in href:
        print(f"  Direct: {href} | Text: {a.get_text().strip()[:50]}")
