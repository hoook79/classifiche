import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Run curl with -I to see headers and redirects
urls = [
    "https://www.earone.it/radio-date/all?year=2026&month=5",
    "https://www.earone.it/radio-date/all?year=2026&month=05",
    "https://www.earone.it/radio-date/all?year=2026"
]

for url in urls:
    print(f"\n--- Checking headers for {url} ---")
    result = subprocess.run(
        ["curl.exe", "-I", "-s", "-L", "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", url],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore'
    )
    print(result.stdout)
