import sys

sys.stdout.reconfigure(encoding='utf-8')

with open("genera_html.py", "r", encoding="utf-8") as f:
    content = f.read()

idx = content.find("function saveYearOverride()")
if idx != -1:
    print(content[idx+1100:idx+2500])
