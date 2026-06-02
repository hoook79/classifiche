import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("genera_html.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "class=\"tab" in line or "onclick=\"switchRadio" in line or "switchRadio" in line:
        print(f"{i+1}: {line.strip()}")
