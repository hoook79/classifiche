import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

urls = [
    "https://radiodate.it/cerca?q=masini",
    "https://radiodate.it/ricerca?q=masini",
    "https://radiodate.it/search?q=masini",
    "https://radiodate.it/cerca.php?q=masini",
    "https://radiodate.it/ricerca.php?q=masini"
]

for url in urls:
    try:
        r = requests.get(url, headers=headers, timeout=5)
        print(f"URL: {url} -> status={r.status_code}, length={len(r.text)}")
        if r.status_code == 200 and "non trovato" not in r.text.lower() and len(r.text) > 5000:
            print("  SUCCESS! This search endpoint exists!")
            print(r.text[:500])
            break
    except Exception as e:
        print(f"Error for {url}: {e}")
