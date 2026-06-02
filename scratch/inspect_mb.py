import requests
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
api_url = "https://musicbrainz.org/ws/2/recording"
headers = {"User-Agent": "RadioMonitor/2.0 (mailto:radio@monitor.it)"}

queries = [
    'recording:"SUPERMAN" AND artist:"FEDERICA ABBATE"',
    'recording:"SUPERMAN" AND artistname:"FEDERICA ABBATE"',
    'SUPERMAN FEDERICA ABBATE'
]

for query in queries:
    print(f"\n--- Query: {query} ---")
    params = {
        "query": query,
        "fmt": "json",
        "limit": 5
    }
    r = requests.get(api_url, params=params, headers=headers, timeout=10)
    if r.status_code != 200:
        print(f"Error {r.status_code}")
        continue
    data = r.json()
    recordings = data.get("recordings", [])
    print(f"Found {len(recordings)} recordings.")
    for idx, rec in enumerate(recordings):
        print(f"\nRecording {idx+1}:")
        print(f"  Title: {rec.get('title')}")
        print(f"  Artist credit: {rec.get('artist-credit')}")
        releases = rec.get("releases", [])
        print(f"  Releases count: {len(releases)}")
        for rel in releases:
            print(f"    Release Title: {rel.get('title')}, Date: {rel.get('date')}")
