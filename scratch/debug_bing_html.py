import requests
from bs4 import BeautifulSoup
import urllib.parse

query = "MARCO MASINI E poi ti ho visto cadere earone"
url_bing = f"https://www.bing.com/search?q={urllib.parse.quote(query)}"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

r = requests.get(url_bing, headers=headers, timeout=10)
soup = BeautifulSoup(r.text, 'html.parser')

print(f"Bing HTML length: {len(r.text)}")
# Troviamo tutti gli elementi che contengono i risultati di ricerca di solito in Bing (es. classe 'b_algo')
results = soup.find_all(class_='b_algo')
print(f"Found {len(results)} elements with class 'b_algo'")

for i, res in enumerate(results[:3]):
    print(f"\n--- RESULT {i+1} ---")
    print(res.get_text()[:400])
    link = res.find('a')
    if link:
        print(f"Link: {link.get('href')}")

# Se 'b_algo' è vuoto, stampiamo un pezzo significativo dell'HTML
if not results:
    print("\n--- FIRST 2000 CHARS OF BODY ---")
    body = soup.find('body')
    if body:
        print(body.get_text()[:2000])
    else:
        print(r.text[:2000])
