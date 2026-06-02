import subprocess
import json
import sys
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

# Test fetching a specific year and month to see if it returns bulk releases
urls = [
    "https://www.earone.it/radio-date/all?year=2026&month=5",
    "https://www.earone.it/radio-date/all?year=2026",
    "https://www.earone.it/radio-date/all?year=2025&month=12"
]

for url in urls:
    print(f"\n--- Fetching {url} ---")
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
            try:
                data = json.loads(large_script[start_idx:end_idx+1])
                page_props = data.get('props', {}).get('pageProps', data.get('pageProps', {}))
                print("pageProps keys:", list(page_props.keys()))
                # See if filteredRadioDate or other lists are populated
                for k in ['filteredRadioDate', 'initialFeedOfAll', 'initialFeedOfToday', 'initialFeedOfFriday']:
                    v = page_props.get(k)
                    if isinstance(v, list) and len(v) > 0:
                        print(f"  {k}: list of length {len(v)}")
                        # print first item sample
                        song = v[0].get('song', {})
                        title = song.get('title') if isinstance(song, dict) else "N/A"
                        # wait, sometimes song is a list, let's see
                        print(f"    First item: {v[0].get('radioDate') or v[0].get('radiodate')} - {title}")
            except Exception as e:
                print("Error parsing JSON:", e)
    else:
        print("pageProps script not found.")
