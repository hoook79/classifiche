import requests
from bs4 import BeautifulSoup

url = "https://onlineradiobox.com/it/divina/playlist/"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
r = requests.get(url, headers=headers)
soup = BeautifulSoup(r.text, 'html.parser')
print(f"Status Code: {r.status_code}")
print("--- TITOLO ---")
print(soup.title.string if soup.title else "Nessun titolo")
print("--- LINKS ---")
for a in soup.find_all('a', href=True):
    print(f"Link: {a['href']} | Text: {a.get_text(strip=True)}")
