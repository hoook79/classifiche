import sys

sys.stdout.reconfigure(encoding='utf-8')

with open("genera_html.py", "r", encoding="utf-8") as f:
    content = f.read()

# Trova la definizione della funzione saveYearOverride in genera_html.py
idx = content.find("function saveYearOverride()")
if idx != -1:
    print("Found 'function saveYearOverride()'!")
    print(content[idx:idx+2500])
else:
    # Se non c'è, cerchiamo "saveYearOverride"
    lines = content.splitlines()
    for i, l in enumerate(lines):
        if "saveYearOverride" in l:
            print(f"{i+1}: {l.strip()}")
