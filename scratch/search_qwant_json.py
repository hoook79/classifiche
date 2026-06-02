import requests
import re
import sys
import urllib.parse

sys.stdout.reconfigure(encoding='utf-8')

query = "MARCO MASINI E poi ti ho visto cadere earone"
url_qwant = f"https://www.qwant.com/?q={urllib.parse.quote(query)}&t=web"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

r = requests.get(url_qwant, headers=headers, timeout=10)

# Cerchiamo tutte le occorrenze di earone
print("Occurrences of earone in HTML:")
matches = [m.start() for m in re.finditer('earone', r.text, re.IGNORECASE)]
for idx in matches[:5]:
    # Stampa 100 caratteri prima e dopo
    print(f"\n--- MATCH AT {idx} ---")
    print(r.text[max(0, idx-150):min(len(r.text), idx+150)])
