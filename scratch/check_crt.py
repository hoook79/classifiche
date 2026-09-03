import requests
from bs4 import BeautifulSoup
import re

def check_crt():
    url = "https://radiocrt.it/playlist-calabria/"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        print(f"CRT Status Code: {r.status_code}")
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Print some interesting elements
        print("\n--- Searching for interesting elements on CRT ---")
        for tag in ['table', 'ul', 'ol', 'div']:
            elements = soup.find_all(tag)
            for el in elements:
                classes = el.get('class', [])
                class_str = " ".join(classes)
                if any(x in class_str.lower() for x in ['track', 'song', 'playlist', 'recent', 'musica', 'brano', 'sched']):
                    print(f"Found {tag} with class: {class_str} (text snippet: {el.get_text(strip=True)[:100]})")
                    
        # Check if there is an iframe
        iframes = soup.find_all('iframe')
        for iframe in iframes:
            print(f"Found iframe: src={iframe.get('src')}")
            
    except Exception as e:
        print(f"Error checking CRT: {e}")

def check_orb(slug):
    url = f"https://onlineradiobox.com/it/{slug}/playlist/"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        rows = soup.select('table.tablelist-schedule tr')
        print(f"ORB {slug}: Status {r.status_code}, Found {len(rows)} tracks")
        if len(rows) > 0:
            first_song = rows[0].select_one('.track_history_item a')
            first_time = rows[0].select_one('.time--schedule')
            if first_song and first_time:
                print(f"  Example track: {first_time.get_text(strip=True)} - {first_song.get_text(strip=True)}")
    except Exception as e:
        print(f"Error checking ORB {slug}: {e}")

if __name__ == "__main__":
    check_crt()
    print("\n--- Checking ORB Slugs ---")
    for slug in ['birikina', 'bruno', 'kisskiss', 'm2o', 'radioproposta']:
        check_orb(slug)
