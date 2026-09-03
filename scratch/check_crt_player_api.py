import requests
import json

def check_player_api():
    url = "https://radiocrt.it/?qtmplayer_json_data="
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        print(f"Status: {r.status_code}")
        print(f"Content length: {len(r.text)}")
        try:
            res_json = r.json()
            print("Response is JSON!")
            print(json.dumps(res_json, indent=2)[:1000])
        except Exception as e:
            print("Response is not JSON!")
            print(r.text[:1000])
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_player_api()
