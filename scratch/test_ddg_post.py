import subprocess
import urllib.parse
from bs4 import BeautifulSoup

query = "ANNALISA Sinceramente earone"
encoded_query = urllib.parse.quote(query)

# Proviamo lite.duckduckgo.com/lite/ con POST (che è il metodo ufficiale per DDG Lite/HTML)
# oppure proviamo html.duckduckgo.com/html/ con POST.
# Di solito DuckDuckGo HTML richiede un POST con 'q' come parametro.

url_html = "https://html.duckduckgo.com/html/"
result = subprocess.run(
    ["curl.exe", "-s", "-L", "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", 
     "-d", f"q={query}", url_html],
    capture_output=True,
    text=True,
    encoding='utf-8',
    errors='ignore'
)

print(f"POST html.duckduckgo.com/html/ Length: {len(result.stdout)}")
soup = BeautifulSoup(result.stdout, 'html.parser')
links = [a['href'] for a in soup.find_all('a', href=True) if 'earone' in a['href']]
print("Links earone:")
for l in links[:5]:
    print(l)

# Proviamo anche lite.duckduckgo.com/lite/ con POST
url_lite = "https://lite.duckduckgo.com/lite/"
result_lite = subprocess.run(
    ["curl.exe", "-s", "-L", "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", 
     "-d", f"q={query}", url_lite],
    capture_output=True,
    text=True,
    encoding='utf-8',
    errors='ignore'
)

print(f"\nPOST lite.duckduckgo.com/lite/ Length: {len(result_lite.stdout)}")
soup_lite = BeautifulSoup(result_lite.stdout, 'html.parser')
links_lite = [a['href'] for a in soup_lite.find_all('a', href=True) if 'earone' in a['href']]
print("Links earone (lite):")
for l in links_lite[:5]:
    print(l)
