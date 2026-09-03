import requests
import re

def check_raw():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    url = "https://radiocrt.it/playlist-calabria/"
    r = requests.get(url, headers=headers, timeout=15)
    
    nonce_match = re.search(r'"nonce"\s*:\s*"([a-zA-Z0-9]+)"', r.text)
    if not nonce_match:
        print("Nonce not found!")
        return
    nonce = nonce_match.group(1)
    
    ajax_url = "https://radiocrt.it/wp-admin/admin-ajax.php"
    
    orderbys = ['date', 'time', 'id', 'modified', 'rand', 'playtime']
    for ob in orderbys:
        data = {
            'action': 'prsidekick-get-history',
            'nonce': nonce,
            'quantity': 5,
            'offset': 0,
            'time_interval': 'all',
            'orderby': ob
        }
        
        r_ajax = requests.post(ajax_url, headers=headers, data=data, timeout=15)
        print(f"\n--- orderby: {ob} ---")
        print(f"Status: {r_ajax.status_code}")
        print(f"Content-Type: {r_ajax.headers.get('Content-Type')}")
        print(f"Raw response (first 200 chars): {r_ajax.text[:200]}")

if __name__ == "__main__":
    check_raw()
