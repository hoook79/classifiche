import requests
from bs4 import BeautifulSoup
import urllib.parse

query = "MARCO MASINI E poi ti ho visto cadere earone"
encoded_query = urllib.parse.quote(query)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# 1. Mojeek
url_mojeek = f"https://www.mojeek.com/search?q={encoded_query}"
try:
    r = requests.get(url_mojeek, headers=headers, timeout=10)
    print(f"Mojeek: status={r.status_code}, length={len(r.text)}")
    soup = BeautifulSoup(r.text, 'html.parser')
    links = [a['href'] for a in soup.find_all('a', href=True) if 'earone' in a['href']]
    print("Earone links (Mojeek):")
    for l in links[:5]:
        print(f"  {l}")
except Exception as e:
    print(f"Mojeek error: {e}")

# 2. Yahoo (proviamo un URL alternativo)
url_yahoo = f"https://it.search.yahoo.com/search?p={encoded_query}"
try:
    r = requests.get(url_yahoo, headers=headers, timeout=10)
    print(f"Yahoo IT: status={r.status_code}, length={len(r.text)}")
    soup = BeautifulSoup(r.text, 'html.parser')
    links = [a['href'] for a in soup.find_all('a', href=True) if 'earone' in a['href']]
    print("Earone links (Yahoo IT):")
    for l in links[:5]:
        print(f"  {l}")
except Exception as e:
    print(f"Yahoo IT error: {e}")

# 3. Qwant
url_qwant = f"https://www.qwant.com/?q={encoded_query}&t=web"
try:
    r = requests.get(url_qwant, headers=headers, timeout=10)
    print(f"Qwant: status={r.status_code}, length={len(r.text)}")
    soup = BeautifulSoup(r.text, 'html.parser')
    links = [a['href'] for a in soup.find_all('a', href=True) if 'earone' in a['href']]
    print("Earone links (Qwant):")
    for l in links[:5]:
        print(f"  {l}")
except Exception as e:
    print(f"Qwant error: {e}")
