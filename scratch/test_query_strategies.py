import subprocess
import json
import sys
import urllib.parse
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

def search_earone(query):
    encoded_query = urllib.parse.quote(query)
    url = f"https://www.earone.it/radio-date/all?search={encoded_query}"
    print(f"Searching: {query} -> {url}")
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
                items = page_props.get('filteredRadioDate', [])
                print(f"Found {len(items)} results:")
                for item in items[:5]:
                    song = item.get('song', {})
                    artists = ", ".join([a.get('name') for a in song.get('tracks', [{}])[0].get('artists', [])]) if song.get('tracks') else "Unknown"
                    print(f"  - {artists} - {song.get('title')} ({item.get('radioDate')})")
                return items
            except Exception as e:
                print("Error parsing JSON:", e)
    else:
        print("No script containing pageProps found.")
    return []

# Test some queries
search_earone("Superstar")
search_earone("Tiziano Ferro Giorgia")
search_earone("Tiziano Ferro Superstar")
search_earone("Coma Cose Posti Vuoti")
