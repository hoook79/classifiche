import requests
from bs4 import BeautifulSoup
import urllib.parse

query = "ANNALISA Sinceramente earone"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# 1. Prova Yahoo
url_yahoo = f"https://search.yahoo.com/search?p={urllib.parse.quote(query)}"
try:
    r_yahoo = requests.get(url_yahoo, headers=headers, timeout=10)
    print(f"Yahoo: status={r_yahoo.status_code}, length={len(r_yahoo.text)}")
    soup = BeautifulSoup(r_yahoo.text, 'html.parser')
    links = [a['href'] for a in soup.find_all('a', href=True) if 'earone' in a['href']]
    print(f"Yahoo found {len(links)} earone links:")
    for l in links[:5]:
        print(f"  {l}")
except Exception as e:
    print(f"Yahoo error: {e}")

# 2. Prova Bing
url_bing = f"https://www.bing.com/search?q={urllib.parse.quote(query)}"
try:
    r_bing = requests.get(url_bing, headers=headers, timeout=10)
    print(f"Bing: status={r_bing.status_code}, length={len(r_bing.text)}")
    soup = BeautifulSoup(r_bing.text, 'html.parser')
    links = [a['href'] for a in soup.find_all('a', href=True) if 'earone' in a['href']]
    print(f"Bing found {len(links)} earone links:")
    for l in links[:5]:
        print(f"  {l}")
except Exception as e:
    print(f"Bing error: {e}")

# 3. Prova Ask.com
url_ask = f"https://www.ask.com/web?q={urllib.parse.quote(query)}"
try:
    r_ask = requests.get(url_ask, headers=headers, timeout=10)
    print(f"Ask.com: status={r_ask.status_code}, length={len(r_ask.text)}")
    soup = BeautifulSoup(r_ask.text, 'html.parser')
    links = [a['href'] for a in soup.find_all('a', href=True) if 'earone' in a['href']]
    print(f"Ask.com found {len(links)} earone links:")
    for l in links[:5]:
        print(f"  {l}")
except Exception as e:
    print(f"Ask error: {e}")
