import requests

def probe_url(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        r = requests.get(url, headers=headers, timeout=5)
        print(f"URL: {url} | Status: {r.status_code} | Length: {len(r.text)} | Content-Type: {r.headers.get('Content-Type')}")
        if r.status_code == 200 and len(r.text) > 0:
            print(f"  Snippet: {r.text[:300]}")
    except Exception as e:
        print(f"URL: {url} | Error: {e}")

if __name__ == "__main__":
    # Test nr6.newradio.it endpoints
    # Stream is https://nr6.newradio.it/proxy/radiomar?mp=/stream
    urls = [
        "https://nr6.newradio.it/proxy/status.xml",
        "https://nr6.newradio.it/status-json.xsl",
        "https://nr6.newradio.it/status.xsl",
        "https://nr6.newradio.it/admin/stats.xml",
        "http://s1.digitalstream.it:8040/status-json.xsl",
        "http://s1.digitalstream.it:8040/played.html",
        "http://s1.digitalstream.it:8040/7.html"
    ]
    for url in urls:
        probe_url(url)
