import requests
import re
import json

def print_all():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    url = "https://radiocrt.it/playlist-calabria/"
    r = requests.get(url, headers=headers, timeout=15)
    
    nonce_match = re.search(r'"nonce"\s*:\s*"([a-zA-Z0-9]+)"', r.text)
    if not nonce_match:
        print("Nonce not found!")
        return
    nonce = nonce_match.group(1)
    
    ajax_url = "https://radiocrt.it/wp-admin/admin-ajax.php"
    data = {
        'action': 'prsidekick-get-history',
        'nonce': nonce,
        'quantity': 50,
        'offset': 0,
        'time_interval': 'all',
        'orderby': 'play'
    }
    
    r_ajax = requests.post(ajax_url, headers=headers, data=data, timeout=15)
    res = r_ajax.json()
    
    print(f"Total items returned: {len(res)}")
    for k, item in res.items():
        song = item.get('song', {})
        artist = song.get('prsidekick_artist')
        title = song.get('prsidekick_song')
        likes = song.get('prsidekick_likes')
        playcount = song.get('prsidekick_play')
        song_id = song.get('id')
        timestamp = item.get(str(song_id))
        print(f"{k}: {artist} - {title} (ID: {song_id}, playcount: {playcount}, timestamp: {timestamp}, likes: {likes})")

if __name__ == "__main__":
    print_all()
