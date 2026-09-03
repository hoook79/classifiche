import re

file_path = r"C:\Users\Jonny\.gemini\antigravity\brain\8e818f01-4c50-4dfd-ab40-95ab5f6238c6\.system_generated\steps\521\content.md"
with open(file_path, "r", encoding="utf-8") as f:
    html = f.read()

terms = ["battiato", "vanzare", "danzare", "this is love", "banderas", "your life"]
for term in terms:
    matches = [m.start() for m in re.finditer(term, html, re.IGNORECASE)]
    print(f"Term '{term}': found {len(matches)} matches")
    for idx in matches:
        print(f"Context: {html[idx-100:idx+200]}")
