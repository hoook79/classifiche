with open('genera_html.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if 'api/override' in line or 'fetch(' in line or 'localhost' in line or 'error' in line:
        if any(keyword in line for keyword in ['fetch', 'api', 'override', 'localhost', 'port']):
            print(f"Line {idx+1}: {line.strip()}")
