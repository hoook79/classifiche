import requests
import re
import json

def test_ajax():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    url = "https://radiocrt.it/playlist-calabria/"
    r = requests.get(url, headers=headers, timeout=15)
    
    # Try finding nonce
    nonce_match = re.search(r'prsidekick_ajax_var\s*=\s*(\{.*?\})', r.text, re.DOTALL)
    if not nonce_match:
        # Fallback to direct nonce search
        nonce_match = re.search(r'"nonce"\s*:\s*"([a-zA-Z0-9]+)"', r.text)
        if nonce_match:
            nonce = nonce_match.group(1)
        else:
            print("Nonce not found!")
            return
    else:
        var_data = json.loads(nonce_match.group(1).replace("'", '"'))
        nonce = var_data['nonce']
        
    print(f"Nonce: {nonce}")
    
    ajax_url = "https://radiocrt.it/wp-admin/admin-ajax.php"
    data = {
        'action': 'prsidekick-get-history',
        'nonce': nonce,
        'quantity': 5,
        'offset': 0,
        'time_interval': 'all',
        'orderby': 'play'
    }
    
    r_ajax = requests.post(ajax_url, headers=headers, data=data, timeout=15)
    data_json = r_ajax.json()
    
    print("\n--- First Item keys and values ---")
    first_key = list(data_json.keys())[0]
    first_item = data_json[first_key]
    print(json.dumps(first_item, indent=2))

if __name__ == "__main__":
    test_ajax()
