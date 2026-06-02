import sys

sys.stdout.reconfigure(encoding='utf-8')

with open("genera_html.py", "r", encoding="utf-8") as f:
    content = f.read()

# Trova la definizione della funzione sortBy in genera_html.py
idx = content.find("function sortBy")
if idx != -1:
    print("Found 'function sortBy'!")
    # Stampiamo i successivi 1500 caratteri
    print(content[idx:idx+2500])
else:
    # Se non c'è "function sortBy", cerchiamo "sortBy" in generale
    lines = content.splitlines()
    for i, l in enumerate(lines):
        if "sortBy" in l:
            print(f"{i+1}: {l.strip()}")
