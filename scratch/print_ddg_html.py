import urllib.parse
import subprocess

query = "ANNALISA Sinceramente earone"
encoded_query = urllib.parse.quote(query)
url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

result = subprocess.run(
    ["curl.exe", "-s", "-L", "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", url],
    capture_output=True,
    text=True,
    encoding='utf-8',
    errors='ignore'
)

print(result.stdout[:2000])
