import requests

try:
    r = requests.get("http://www.radiodate.it/", timeout=5)
    print(f"Status: {r.status_code}, length={len(r.text)}")
    print(r.text[:500])
except Exception as e:
    print(f"Error: {e}")
