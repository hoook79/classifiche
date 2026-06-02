import requests
from bs4 import BeautifulSoup

def get_songs(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, 'html.parser')
    rows = soup.select('table.tablelist-schedule tr')
    results = []
    for row in rows:
        time_el = row.select_one('.time--schedule')
        song_el = row.select_one('.track_history_item a')
        if time_el and song_el:
            results.append((time_el.get_text(strip=True), song_el.get_text(strip=True)))
    return results[:10]

if __name__ == "__main__":
    print("--- Main Playlist ---")
    for s in get_songs("https://onlineradiobox.com/it/divina/playlist/"):
        print(s)
    print("\n--- /1 Playlist ---")
    for s in get_songs("https://onlineradiobox.com/it/divina/playlist/1"):
        print(s)
    print("\n--- /2 Playlist ---")
    for s in get_songs("https://onlineradiobox.com/it/divina/playlist/2"):
        print(s)
