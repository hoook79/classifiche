import requests
from bs4 import BeautifulSoup

url = "https://onlineradiobox.com/it/m2o/playlist/"
headers = {'User-Agent': 'Mozilla/5.0'}
try:
    r = requests.get(url, headers=headers, timeout=10)
    print(f"Status Code: {r.status_code}")
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, 'html.parser')
        rows = soup.select('table.tablelist-schedule tr')
        print(f"Trovate {len(rows)} righe su OnlineRadioBox.")
        for i, row in enumerate(rows[:5]):
            time_el = row.select_one('.time--schedule')
            song_el = row.select_one('.track_history_item a')
            if time_el and song_el:
                print(f"  {time_el.get_text(strip=True)}: {song_el.get_text(strip=True)}")
except Exception as e:
    print(f"Errore: {e}")
