import sys

sys.stdout.reconfigure(encoding='utf-8')

with open("genera_html.py", "r", encoding="utf-8") as f:
    content = f.read()

lines = content.splitlines()
keywords = ["activex", "wscript", "shell", "exec", "subprocess", "cmd", "bat", "system", "run", "launch", "protocol"]
for idx, line in enumerate(lines):
    line_lower = line.lower()
    for kw in keywords:
        if kw in line_lower and ("script" in line_lower or "function" in line_lower or "fetch" in line_lower or "xhr" in line_lower or "ajax" in line_lower or "click" in line_lower):
            print(f"Line {idx+1}: {line.strip()}")
            break
