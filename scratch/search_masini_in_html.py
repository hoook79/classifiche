import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

html_path = "classifica_radio.html"
if os.path.exists(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Cerca tutte le ricorrenze di "masini"
    import re
    matches = [m.start() for m in re.finditer("masini", content, re.IGNORECASE)]
    print(f"Found {len(matches)} occurrences of 'masini' in HTML:")
    for idx in matches[:5]:
        start = max(0, idx - 100)
        end = min(len(content), idx + 100)
        print(f"\nOccurrence at index {idx}:")
        print(content[start:end].strip())
else:
    print(f"HTML file {html_path} not found.")
