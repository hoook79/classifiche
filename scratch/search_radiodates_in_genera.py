import sys

sys.stdout.reconfigure(encoding='utf-8')

with open("genera_html.py", "r", encoding="utf-8") as f:
    content = f.read()

lines = content.splitlines()
found = False
for idx, line in enumerate(lines):
    if "CACHE_RADIODATES" in line or "radiodate" in line.lower() or "radio_date" in line.lower():
        print(f"{idx+1}: {line.strip()}")
        found = True

if not found:
    print("No references found.")
