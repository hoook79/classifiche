import subprocess
import re
import sys
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

url = "https://www.earone.it/radio-date/all"
result = subprocess.run(
    ["curl.exe", "-s", "-L", "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", url],
    capture_output=True,
    text=True,
    encoding='utf-8',
    errors='ignore'
)

html = result.stdout
soup = BeautifulSoup(html, 'html.parser')

print("=== Year / Month Selectors or Links ===")
# Find all <a> tags that look like they go to radio_date or have year/month in href
links = set()
for a in soup.find_all('a', href=True):
    href = a['href']
    if 'radio' in href or 'date' in href or re.search(r'\d{4}', href):
        links.add(href)

for l in sorted(links):
    print("Link:", l)
