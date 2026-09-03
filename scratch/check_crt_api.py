import requests
import re

url_js = "https://radiocrt.it/wp-content/plugins/proradio-sidekick/js/prsidekick-min.js?ver=9.1"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
r = requests.get(url_js, headers=headers)
js_content = r.text

print("--- Printing context of prsidekick-get-history ---")
idx = 0
while True:
    idx = js_content.find("prsidekick-get-history", idx)
    if idx == -1:
        break
    start = max(0, idx - 500)
    end = min(len(js_content), idx + 500)
    print(f"\n--- MATCH AT INDEX {idx} ---")
    print(js_content[start:end])
    idx += len("prsidekick-get-history")
