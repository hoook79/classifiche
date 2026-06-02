import requests
from bs4 import BeautifulSoup

query = "ANNALISA Sinceramente earone"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# Proviamo a fare un GET su html.duckduckgo.com/html/
url_get = "https://html.duckduckgo.com/html/"
r = requests.get(url_get, params={'q': query}, headers=headers, timeout=10)
print(f"GET requests Length: {len(r.text)}")

soup = BeautifulSoup(r.text, 'html.parser')
links = []
for a in soup.find_all('a', href=True):
    href = a['href']
    if 'earone' in href:
        links.append(href)

print("Links earone:")
for l in links[:5]:
    print(l)

# Proviamo a fare un POST su html.duckduckgo.com/html/
r_post = requests.post("https://html.duckduckgo.com/html/", data={'q': query}, headers=headers, timeout=10)
print(f"\nPOST requests Length: {len(r_post.text)}")
soup_post = BeautifulSoup(r_post.text, 'html.parser')
links_post = []
for a in soup_post.find_all('a', href=True):
    href = a['href']
    if 'earone' in href:
        links_post.append(href)

print("Links earone (post):")
for l in links_post[:5]:
    print(l)
