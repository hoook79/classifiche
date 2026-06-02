import urllib.request
import urllib.parse
import json

APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbx_p44hQCjBjPvNOdM5whPI3hgd8SA96gbAcwva3ywe8CRjci4RAYUQXYc4oVMuzEic/exec"

def test_api():
    # Test Login
    login_params = {
        'action': 'login',
        'username': 'Max',
        'password': 'test123'
    }
    url_login = f"{APPS_SCRIPT_URL}?{urllib.parse.urlencode(login_params)}"
    
    print("Test Login...")
    try:
        with urllib.request.urlopen(url_login) as response:
            res_data = response.read().decode('utf-8')
            print("Login Response:")
            print(json.dumps(json.loads(res_data), indent=2))
    except Exception as e:
        print(f"Errore login: {e}")

    # Test getData
    data_params = {
        'action': 'getData',
        'username': 'Max',
        'password': 'test123'
    }
    url_data = f"{APPS_SCRIPT_URL}?{urllib.parse.urlencode(data_params)}"
    
    print("\nTest getData...")
    try:
        with urllib.request.urlopen(url_data) as response:
            res_data = response.read().decode('utf-8')
            res_json = json.loads(res_data)
            print("getData Response keys inside 'data':", list(res_json.get('data', {}).keys()))
            print("getData Response allowedRadios:", res_json.get('allowedRadios'))
            print("getData success:", res_json.get('success'))
    except Exception as e:
        print(f"Errore getData: {e}")

if __name__ == '__main__':
    test_api()
