import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("genera_html.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "tutte" in line.lower() or "aggregate" in line.lower() or "combine" in line.lower() or "unific" in line.lower() or "merged" in line.lower():
        print(f"{i+1}: {line.strip()}")
