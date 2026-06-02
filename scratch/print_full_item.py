import subprocess
import json
import sys
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

url = "https://www.earone.it/radio-date/all?search=Tiziano"
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
    start_idx = large_script.find('{')
    end_idx = large_script.rfind('}')
    if start_idx != -1 and end_idx != -1:
        data = json.loads(large_script[start_idx:end_idx+1])
        page_props = data.get('props', {}).get('pageProps', data.get('pageProps', {}))
        items = page_props.get('filteredRadioDate', [])
        if items:
            print(json.dumps(items[0], indent=2, ensure_ascii=False))
            print("\n" + "="*40 + "\n")
            print(json.dumps(items[1], indent=2, ensure_ascii=False))
