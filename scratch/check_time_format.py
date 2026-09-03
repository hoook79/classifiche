import requests
import re

url_js = "https://radiocrt.it/wp-content/plugins/proradio-sidekick/js/prsidekick-min.js?ver=9.1"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
r = requests.get(url_js, headers=headers)
js = r.text

idx = js.find("prsidekick-get-history")
if idx != -1:
    success_idx = js.find("success:function", idx)
    if success_idx != -1:
        # Print the next 2000 characters of the success callback
        print(js[success_idx:success_idx+2500])
