import requests
import json

url = "https://script.google.com/macros/s/AKfycbx_p44hQCjBjPvNOdM5whPI3hgd8SA96gbAcwva3ywe8CRjci4RAYUQXYc4oVMuzEic/exec"
print(f"Testing connection to Google Apps Script at URL: {url}...")

# Test getData action with dummy credentials
params = {
    "action": "getData",
    "username": "dummy_test_user",
    "password": "dummy_test_password"
}

try:
    response = requests.get(url, params=params, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Response URL: {response.url}")
    print("Response headers:")
    for h, v in response.headers.items():
        print(f"  {h}: {v}")
    
    print("\nResponse Body (first 500 chars):")
    print(response.text[:500])
    
    # Try to parse as JSON
    try:
        data = response.json()
        print("\nSuccessfully parsed as JSON:")
        print(json.dumps(data, indent=2)[:500])
    except Exception as je:
        print(f"\nFailed to parse response as JSON: {je}")
except Exception as e:
    print(f"Connection failed: {e}")
