import re
import os
import subprocess

html_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'index.html')
print(f"Reading {html_path}...")

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find all script blocks in HTML
scripts = re.findall(r'<script\b[^>]*>(.*?)</script>', content, re.DOTALL)

print(f"Found {len(scripts)} script blocks.")

for i, script in enumerate(scripts):
    # Only test scripts that contain javascript logic (exclude data/JSON if any)
    if "function" in script or "const" in script or "let" in script or "var" in script:
        # Write to a temp file
        temp_js = f"temp_script_{i}.js"
        with open(temp_js, 'w', encoding='utf-8') as js_f:
            js_f.write(script)
        
        # Check syntax using Node.js
        res = subprocess.run(['node', '--check', temp_js], capture_output=True, text=True)
        if res.returncode != 0:
            print(f"\n[SYNTAX ERROR] found in script block {i}:")
            print(res.stderr)
            # Print a few lines around the error line if possible
            # Node error formats line number in file: line number is after temp_js:LINE
            match = re.search(r'temp_script_\d+\.js:(\d+)', res.stderr)
            if match:
                err_line = int(match.group(1))
                lines = script.split('\n')
                start = max(0, err_line - 10)
                end = min(len(lines), err_line + 10)
                print(f"Showing lines {start+1} to {end} around the error:")
                for idx in range(start, end):
                    print(f"{idx+1}: {lines[idx]}")
        else:
            print(f"Script block {i}: Syntax OK")
        
        # Clean up temp file
        if os.path.exists(temp_js):
            os.remove(temp_js)
