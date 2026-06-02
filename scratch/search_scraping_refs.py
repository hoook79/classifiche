import os

for root, dirs, files in os.walk('.'):
    for f in files:
        if f.endswith('.py') or f.endswith('.bat'):
            path = os.path.join(root, f)
            try:
                with open(path, 'r', encoding='utf-8') as file_obj:
                    content = file_obj.read()
                    if 'scrape_recent.py' in content or 'scrape_earone_radiodates' in content:
                        print(f"Found in {path}")
            except Exception:
                pass
