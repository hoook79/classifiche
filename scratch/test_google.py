import requests
import subprocess
import urllib.parse
from bs4 import BeautifulSoup

query = "ANNALISA Sinceramente earone"
encoded_query = urllib.parse.quote(query)

# 1. Prova Google con requests (standard desktop user agent)
headers_desktop = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}
url_google = f"https://www.google.com/search?q={encoded_query}"
r = requests.get(url_google, headers=headers_desktop, timeout=10)
print(f"Google Requests (Desktop) status={r.status_code}, length={len(r.text)}")
soup = BeautifulSoup(r.text, 'html.parser')
links = [a['href'] for a in soup.find_all('a', href=True) if 'earone' in a['href']]
print("Earone links (Desktop):")
for l in links[:5]:
    print(f"  {l}")

# 2. Prova Google con requests (mobile/old user agent - Google spesso restituisce HTML super leggero senza JS per user agent vecchi)
headers_old = {
    'User-Agent': 'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)'
}
r_old = requests.get(url_google, headers=headers_old, timeout=10)
print(f"\nGoogle Requests (IE9) status={r_old.status_code}, length={len(r_old.text)}")
soup_old = BeautifulSoup(r_old.text, 'html.parser')
links_old = [a['href'] for a in soup_old.find_all('a', href=True) if 'earone' in a['href']]
print("Earone links (IE9):")
for l in links_old[:5]:
    print(f"  {l}")

# 3. Prova Google tramite curl.exe
result = subprocess.run(
    ["curl.exe", "-s", "-L", "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", url_google],
    capture_output=True,
    text=True,
    encoding='utf-8',
    errors='ignore'
)
print(f"\nGoogle curl status length={len(result.stdout)}")
soup_curl = BeautifulSoup(result.stdout, 'html.parser')
links_curl = [a['href'] for a in soup_curl.find_all('a', href=True) if 'earone' in a['href']]
print("Earone links (curl):")
for l in links_curl[:5]:
    print(f"  {l}")
