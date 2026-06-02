import sys
import os
import re

sys.stdout.reconfigure(encoding='utf-8')

html_path = "classifica_radio.html"
if os.path.exists(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    matches = [m.start() for m in re.finditer("cadere", content, re.IGNORECASE)]
    print(f"Found {len(matches)} occurrences of 'cadere' in HTML:")
    for idx in matches:
        start = max(0, idx - 150)
        end = min(len(content), idx + 150)
        print(f"\nOccurrence at index {idx}:")
        print(content[start:end].strip())
else:
    print(f"HTML file {html_path} not found.")
