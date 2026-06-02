import subprocess
from bs4 import BeautifulSoup
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = "https://earone.com/post/65fe0daffb58"
print(f"Fetching: {url}...")

result = subprocess.run(
    ["curl.exe", "-s", "-L", "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", url],
    capture_output=True,
    text=True,
    encoding='utf-8',
    errors='ignore'
)

print(f"Response length: {len(result.stdout)}")

# Let's inspect the page content or redirects
# We can search for the text or search for a date format in the body
soup = BeautifulSoup(result.stdout, 'html.parser')
page_text = soup.get_text()

print("\nSearching for dates in text...")
# Cerca DD/MM/YYYY o DD-MM-YYYY (supportando anche l'assenza di word boundaries \b)
match_text = re.search(r'(?<!\d)(\d{2})/(\d{2})/(\d{4})(?!\d)', page_text)
if match_text:
    print(f"Found standard date: {match_text.group(0)}")

match_text_dash = re.search(r'(?<!\d)(\d{2})-(\d{2})-(\d{4})(?!\d)', page_text)
if match_text_dash:
    print(f"Found dashed date: {match_text_dash.group(0)}")

# Cerca formato con mese in italiano (es. 23 gennaio 2026)
months_it = {
    'gennaio': '01', 'febbraio': '02', 'marzo': '03', 'aprile': '04',
    'maggio': '05', 'giugno': '06', 'luglio': '07', 'agosto': '08',
    'settembre': '09', 'ottobre': '10', 'novembre': '11', 'dicembre': '12'
}
months_pattern = '|'.join(months_it.keys())
match_it = re.search(r'(?<!\d)(\d{1,2})\s+(' + months_pattern + r')\s+(\d{4})(?!\d)', page_text, re.IGNORECASE)
if match_it:
    print(f"Found Italian month date: {match_it.group(0)}")
    
# Let's print the entire text to see what is inside
print("\n--- BODY TEXT ---")
print(page_text[:3000])
