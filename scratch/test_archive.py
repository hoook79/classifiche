import requests

slug = "subasio"
target_url = f"https://onlineradiobox.com/it/{slug}/playlist/"
timestamp = "20260510235959"  # Fine giornata del 10 Maggio 2026

api_url = f"https://archive.org/wayback/available?url={target_url}&timestamp={timestamp}"
r = requests.get(api_url)
print("Wayback Response:", r.status_code)
if r.status_code == 200:
    data = r.json()
    snapshots = data.get("archived_snapshots", {})
    closest = snapshots.get("closest", {})
    if closest and closest.get("available"):
        print("Snapshot URL:", closest.get("url"))
        print("Snapshot Timestamp:", closest.get("timestamp"))
    else:
        print("No snapshots found")
else:
    print("API Error")
