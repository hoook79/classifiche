import subprocess
import json
import sys
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

url = "https://www.earone.it/radio-date/all"
print("Fetching:", url)
result = subprocess.run(
    ["curl.exe", "-s", "-L", "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", url],
    capture_output=True,
    text=True,
    encoding='utf-8',
    errors='ignore'
)

html = result.stdout
soup = BeautifulSoup(html, 'html.parser')

large_script = None
for s in soup.find_all('script'):
    text = s.string or ''
    if len(text) > 1000 and 'pageProps' in text:
        large_script = text
        break

if large_script:
    print("Found script!")
    # Let's clean the script to get just the JSON. On Next.js pages, it is in <script id="__NEXT_DATA__" type="application/json">...</script>
    next_data_script = soup.find('script', id='__NEXT_DATA__')
    if next_data_script:
        data = json.loads(next_data_script.string)
    else:
        # try parsing the large_script raw string if it has a JSON structure
        # usually next data is perfect
        data = json.loads(large_script)
        
    page_props = data.get('props', {}).get('pageProps', data.get('pageProps', {}))
    print("pageProps keys:", list(page_props.keys()))
    for k, v in page_props.items():
        if isinstance(v, list) and len(v) > 0:
            print(f"  List key: {k}, length: {len(v)}")
            print("    First item sample:")
            print("   ", str(v[0])[:300])
else:
    print("Could not find script with pageProps.")
