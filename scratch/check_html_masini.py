import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

html_path = "classifica_radio.html"
if os.path.exists(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        # We can read chunk by chunk or search
        content = f.read()
    
    # Cerca il pezzo di JS o HTML contenente la canzone
    idx = content.find("E poi ti ho visto cadere")
    if idx != -1:
        print("Trovato riferimento nel file HTML!")
        # Stampiamo i dintorni del testo trovato (es. 200 caratteri prima e dopo)
        start = max(0, idx - 200)
        end = min(len(content), idx + 200)
        print(content[start:end])
    else:
        print("Riferimento alla canzone non trovato nel file HTML.")
else:
    print(f"HTML file {html_path} not found.")
