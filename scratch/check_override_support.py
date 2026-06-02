with open('genera_html.py', 'r', encoding='utf-8') as f:
    content = f.read()

if 'manual_radiodates_override.json' in content:
    print("Found in genera_html.py!")
else:
    print("NOT found in genera_html.py!")
