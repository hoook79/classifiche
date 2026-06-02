import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

for root, dirs, files in os.walk("."):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            if "normalize_name" in content:
                print(f"--- {path} ---")
                lines = content.splitlines()
                for idx, line in enumerate(lines):
                    if "normalize_name" in line:
                        print(f"  {idx+1}: {line.strip()}")
