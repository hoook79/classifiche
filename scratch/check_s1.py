import requests
import json

url = "http://s1.digitalstream.it:8040/status-json.xsl"
r = requests.get(url)
print(json.dumps(r.json(), indent=2))
