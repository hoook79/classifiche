import subprocess
import os
from bs4 import BeautifulSoup
import urllib.parse

query = "ANNALISA Sinceramente earone"
encoded_query = urllib.parse.quote(query)
url1 = f"https://www.google.it/search?q={encoded_query}&gbv=1"

cookie_file = "scratch_cookies.txt"
if os.path.exists(cookie_file):
    os.remove(cookie_file)

# Inizializziamo il file dei cookie con SOCS (GDPR bypass)
# Formato Netscape cookie file
with open(cookie_file, "w") as f:
    f.write("# Netscape HTTP Cookie File\n")
    f.write(".google.it\tTRUE\t/\tFALSE\t2082758400\tSOCS\tCAESHAgBEhJnd2NfMjAyNDA4MTktUkNfMF8xGgJpdCABIContent\n")
    f.write(".google.com\tTRUE\t/\tFALSE\t2082758400\tSOCS\tCAESHAgBEhJnd2NfMjAyNDA4MTktUkNfMF8xGgJpdCABIContent\n")

print(f"Querying Google Page 1...")
result1 = subprocess.run(
    ["curl.exe", "-s", "-L", "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", 
     "-c", cookie_file, "-b", cookie_file, url1],
    capture_output=True,
    text=True,
    encoding='utf-8',
    errors='ignore'
)

print(f"Page 1: length={len(result1.stdout)}")

soup1 = BeautifulSoup(result1.stdout, 'html.parser')
redirect_link = None
for a in soup1.find_all('a', href=True):
    href = a['href']
    if href.startswith('/search?'):
        redirect_link = href
        break

if redirect_link:
    url2 = "https://www.google.it" + redirect_link
    print(f"Following redirect via curl: {url2}")
    
    result2 = subprocess.run(
        ["curl.exe", "-s", "-L", "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", 
         "-c", cookie_file, "-b", cookie_file, url2],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore'
    )
    
    print(f"Page 2: length={len(result2.stdout)}")
    
    # Controlliamo i cookie salvati nel file
    with open(cookie_file, "r") as f:
        print("\nCookies saved in file:")
        print(f.read())
        
    soup2 = BeautifulSoup(result2.stdout, 'html.parser')
    links = []
    for a in soup2.find_all('a', href=True):
        href = a['href']
        if href.startswith('/url?q='):
            parsed = urllib.parse.urlparse(href)
            query_params = urllib.parse.parse_qs(parsed.query)
            if 'q' in query_params:
                actual_url = query_params['q'][0]
                if 'earone' in actual_url:
                    links.append(actual_url)
                    
    print(f"\nFound {len(links)} earone links:")
    for l in links:
        print(f"  -> {l}")
        
    if not links:
        print("\n--- BODY TEXT OF RESULTS PAGE ---")
        print(soup2.get_text()[:1000])
else:
    print("No redirect URL found!")
