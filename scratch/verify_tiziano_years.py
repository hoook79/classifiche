import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Let's inspect the compiled HTML file by searching the embedded JSON variables
with open("classifica_radio.html", "r", encoding="utf-8") as f:
    content = f.read()

# Let's extract the RAW object
match = re.search(r'const\s+RAW\s*=\s*(\{.*?\});\s*const', content, re.DOTALL)
if match:
    json_str = match.group(1)
    # Since it's very large, let's parse keys one by one or find Tiziano
    # Let's find Tiziano Superstar in the json_str using regex
    # Each song in RAW has format {"artist":"...","title":"...","year":"...","radioDate":"..."}
    pattern = r'\{"artist":"[^"]*?tiziano[^"]*?","title":"[^"]*?superstar[^"]*?",.*?\}'
    matches = re.findall(pattern, json_str, re.IGNORECASE)
    print("Found matching songs in HTML:")
    for m in matches:
        # try to parse as JSON
        try:
            song = json.loads(m)
            print(f"  Artist: {song.get('artist')} | Title: {song.get('title')} | Year: {song.get('year')} | Radio Date: {song.get('radioDate')}")
        except Exception as e:
            print("  Raw match:", m)
else:
    # Let's search via raw string search in the whole HTML
    print("RAW variable structure not matched by general regex. Searching raw string...")
    # Find all occurrences of Tiziano and Superstar in close proximity
    pattern = r'\{"artist":"[^"]*?Tiziano[^"]*?","title":"Superstar"[^\}]*?\}'
    matches = re.findall(pattern, content, re.IGNORECASE)
    for m in matches:
        print("  Raw:", m)
