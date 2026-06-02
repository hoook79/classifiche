import requests
from bs4 import BeautifulSoup

url = "https://radiodate.it/"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

r = requests.get(url, headers=headers, timeout=10)
soup = BeautifulSoup(r.text, 'html.parser')

print("FORM ACTIONS:")
for form in soup.find_all('form'):
    print(f"Form action: {form.get('action')} | method: {form.get('method')}")
    for inp in form.find_all('input'):
        print(f"  Input: name={inp.get('name')} | type={inp.get('type')}")

print("\nTOP LINKS IN RADIODATE.IT:")
count = 0
for a in soup.find_all('a', href=True):
    href = a['href']
    text = a.get_text().strip()
    if href.startswith('http') or '/' in href:
        print(f"  Href: {href} | Text: {text[:50]}")
        count += 1
        if count >= 30:
            break
