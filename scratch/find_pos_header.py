import sys

sys.stdout.reconfigure(encoding='utf-8')

with open("genera_html.py", "r", encoding="utf-8") as f:
    content = f.read()

# Trova tutti i tag <th> che contengono la parola "Posizione" o "Pos"
lines = content.splitlines()
for idx, line in enumerate(lines):
    if "posizione" in line.lower() and "th" in line.lower():
        print(f"Line {idx+1}: {line.strip()}")
