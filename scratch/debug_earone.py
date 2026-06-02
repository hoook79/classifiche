import sys
sys.path.append(r'c:\Users\Jonny\Desktop\REPORT CANZONI RADIO')
from scrape_earone_radiodates import fetch_earone_page
from bs4 import BeautifulSoup

url = "https://earone.com/post/65fe0daffb58"
print(f"Scaricamento di {url}...")
html = fetch_earone_page(url)
print(f"Lunghezza HTML scaricato: {len(html)}")

soup = BeautifulSoup(html, 'html.parser')
print("\n--- TESTO ESTRATTO ---")
text = soup.get_text()
print(text[:2000])
