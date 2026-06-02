import urllib.parse
import subprocess
from bs4 import BeautifulSoup

query = "ANNALISA Sinceramente earone"
encoded_query = urllib.parse.quote(query)
url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

print(f"Querying DuckDuckGo: {url}")
result = subprocess.run(
    ["curl.exe", "-s", "-L", "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", url],
    capture_output=True,
    text=True,
    encoding='utf-8',
    errors='ignore'
)

print(f"HTML Length: {len(result.stdout)}")
soup = BeautifulSoup(result.stdout, 'html.parser')

links = []
for a in soup.find_all('a', href=True):
    href = a['href']
    links.append(href)

print(f"Total links found: {len(links)}")
for l in links[:30]:
    print(f"Link: {l}")
