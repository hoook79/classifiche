import requests
import re
import json

def test_params():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    url = "https://radiocrt.it/playlist-calabria/"
    r = requests.get(url, headers=headers, timeout=15)
    
    nonce_match = re.search(r'"nonce"\s*:\s*"([a-zA-Z0-9]+)"', r.text)
    if not nonce_match:
        print("Nonce not found!")
        return
    nonce = nonce_match.group(1)
    
    ajax_url = "https://radiocrt.it/wp-admin/admin-ajax.php"
    
    # Let's try some parameters
    configs = [
        {'orderby': 'play', 'time_interval': 'all', 'label': 'Default (play, all)'},
        {'orderby': 'date', 'time_interval': 'all', 'label': 'date, all'},
        {'orderby': 'playtime', 'time_interval': 'all', 'label': 'playtime, all'},
        {'orderby': 'recent', 'time_interval': 'all', 'label': 'recent, all'},
        {'orderby': 'play', 'time_interval': 'today', 'label': 'play, today'},
        {'orderby': 'date', 'time_interval': 'today', 'label': 'date, today'},
    ]
    
    for cfg in configs:
        data = {
            'action': 'prsidekick-get-history',
            'nonce': nonce,
            'quantity': 5,
            'offset': 0,
            'time_interval': cfg['time_interval'],
            'orderby': cfg['orderby']
        }
        
        r_ajax = requests.post(ajax_url, headers=headers, data=data, timeout=15)
        try:
            res = r_ajax.json()
            print(f"\n--- Config: {cfg['label']} ---")
            print(f"Keys returned: {list(res.keys())[:5]}")
            # print the first item
            first_key = list(res.keys())[0]
            item = res[first_key]
            # Print song title and if there is any timestamp field (a field matching the song id)
            song = item.get('song', {})
            song_id = str(song.get('id', ''))
            playtime_val = item.get(song_id)
            print(f"Song: {song.get('prsidekick_artist')} - {song.get('prsidekick_song')} (ID: {song_id})")
            print(f"Timestamp field value: {playtime_val}")
        except Exception as e:
            print(f"Failed config {cfg['label']}: {e}")

if __name__ == "__main__":
    test_params()
