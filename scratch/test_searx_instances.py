import requests
from bs4 import BeautifulSoup
import urllib.parse
import sys

sys.stdout.reconfigure(encoding='utf-8')

query = "MARCO MASINI E poi ti ho visto cadere earone"
encoded_query = urllib.parse.quote(query)

instances = [
    f"https://searx.work/search?q={encoded_query}",
    f"https://searx.space/search?q={encoded_query}",
    f"https://northboot.xyz/searx/search?q={encoded_query}",
    f"https://priv.au/search?q={encoded_query}",
    f"https://searx.or.id/search?q={encoded_query}",
    f"https://searx.mx/search?q={encoded_query}"
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

for url in instances:
    print(f"\nQuerying Searx instance: {url}")
    try:
        r = requests.get(url, headers=headers, timeout=8)
        print(f"Response: status={r.status_code}, length={len(r.text)}")
        if r.status_code == 200 and len(r.text) > 3000:
            soup = BeautifulSoup(r.text, 'html.parser')
            links = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                if 'earone' in href:
                    links.append(href)
            print(f"Found {len(links)} earone links:")
            for l in links[:5]:
                print(f"  -> {l}")
            if links:
                print("SUCCESSFUL INSTANCE FOUND!")
                break
    except Exception as e:
        print(f"Error: {e}")
