with open('genera_html.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if 'server.py' in line or 'bat' in line or 'cmd' in line:
        print(f"Line {idx+1}: {line.strip()}")
