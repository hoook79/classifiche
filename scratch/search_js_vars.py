import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open("genera_html.py", "r", encoding="utf-8") as f:
    content = f.read()

# Let's search for "RAW" or the variables like "json_subasio"
for line in content.splitlines():
    if "json_subasio" in line or "json_toscana" in line or "const RAW =" in line or "RAW =" in line:
        print(line)
