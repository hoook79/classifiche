import subprocess
import json
import sys
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

url = "https://www.earone.it/radio-date/all?search=Tiziano"
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
    # On Next.js pages, let's extract the JSON block. It usually starts with { and ends with }
    # and is inside a self-invoking function or script block.
    # Let's find first '{' and last '}'
    start_idx = large_script.find('{')
    end_idx = large_script.rfind('}')
    if start_idx != -1 and end_idx != -1:
        try:
            json_data = large_script[start_idx:end_idx+1]
            data = json.loads(json_data)
            page_props = data.get('props', {}).get('pageProps', data.get('pageProps', {}))
            print("pageProps keys:", list(page_props.keys()))
            for k, v in page_props.items():
                if isinstance(v, list) and len(v) > 0 and k not in ['years', 'months', 'genre', 'nationality']:
                    print(f"  {k} (length {len(v)}):")
                    for idx, item in enumerate(v[:5]):
                        print(f"    Item {idx+1}: {str(item)[:400]}")
        except Exception as e:
            print("Error parsing JSON:", e)
else:
    print("Could not find script with pageProps.")
