import requests
import urllib.parse
import sys

sys.stdout.reconfigure(encoding='utf-8')

query = "MARCO MASINI E poi ti ho visto cadere earone"
encoded_query = urllib.parse.quote(query)
url = f"https://api.qwant.com/v3/search/web?q={encoded_query}&locale=it_it&count=10&t=web"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

try:
    r = requests.get(url, headers=headers, timeout=10)
    print(f"Qwant API: status={r.status_code}, length={len(r.text)}")
    data = r.json()
    
    results = data.get('data', {}).get('result', {}).get('items', [])
    print(f"Found {len(results)} items in API response:")
    
    links = []
    for item in results:
        url_res = item.get('url', '')
        title = item.get('title', '')
        print(f"  Title: {title} | Url: {url_res}")
        if 'earone' in url_res:
            links.append(url_res)
            
    print(f"\nFound {len(links)} earone links:")
    for l in links:
        print(f"  -> {l}")
        
except Exception as e:
    print(f"Qwant API error: {e}")
