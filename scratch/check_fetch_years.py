import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("fetch_years.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "def " in line or "clean" in line or "normalize" in line or ".get(" in line or "_cache" in line:
        print(f"{idx+1}: {line.strip()}")
