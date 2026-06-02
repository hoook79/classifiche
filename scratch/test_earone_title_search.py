import urllib.parse
import subprocess
import json
import sys
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

def search_earone(query):
    encoded_query = urllib.parse.quote(query)
    url = f"https://www.earone.it/radio-date/all?search={encoded_query}"
    print(f"Querying EarOne: {url}")
    result = subprocess.run(
        ["curl.exe", "-s", "-L", "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", url],
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
                return page_props.get('filteredRadioDate', [])
            except Exception as e:
                print(f"Error parsing JSON: {e}")
    return []

# Test con il solo titolo
test_titles = [
    "E poi ti ho visto cadere",
    "XXDONO",
    "L'Ultimo Addio"
]

for title in test_titles:
    print(f"\nSearching for title: '{title}'")
    results = search_earone(title)
    print(f"Found {len(results)} results:")
    for res in results[:3]:
        song_info = res.get('song', {})
        res_title = song_info.get('title')
        res_artists = ", ".join([a.get('name') for a in song_info.get('tracks', [{}])[0].get('artists', [])]) if song_info.get('tracks') else "Unknown"
        print(f"  Artist: {res_artists} | Title: {res_title} | RadioDate: {res.get('radioDate')}")
