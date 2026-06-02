import subprocess
import urllib.parse
from bs4 import BeautifulSoup
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

query = "MARCO MASINI E poi ti ho visto cadere earone"
encoded_query = urllib.parse.quote(query)
url = f"https://search.yahoo.com/search?p={encoded_query}"

print("Querying Yahoo with curl.exe...")
result = subprocess.run(
    ["curl.exe", "-s", "-L", "-A", "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1", url],
    capture_output=True,
    text=True,
    encoding='utf-8',
    errors='ignore'
)

print(f"Status Code: {result.returncode}")
print(f"Length of response: {len(result.stdout)}")

if len(result.stdout) > 1000:
    soup = BeautifulSoup(result.stdout, 'html.parser')
    links = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        if 'earone' in href:
            links.append(href)
    print(f"Found {len(links)} earone links:")
    for l in links[:10]:
        print(f"  {l}")
else:
    print("Response too short. Let's see the first 500 chars:")
    print(result.stdout[:500])
