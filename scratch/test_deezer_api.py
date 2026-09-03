import requests

album_id = 303743
url = f"https://api.deezer.com/album/{album_id}"

r = requests.get(url)
print("Album Status:", r.status_code)
if r.status_code == 200:
    data = r.json()
    print("Label:", data.get("label"))
    print("Release Date:", data.get("release_date"))
    print("Genre ID:", data.get("genre_id"))
    print("Album keys:", data.keys())
else:
    print("Failed to get album details")
