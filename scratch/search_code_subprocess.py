import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

for root, dirs, files in os.walk("."):
    for file in files:
        if file.endswith(".py") or file.endswith(".bat") or file.endswith(".html"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            if "CREATE_NO_WINDOW" in content or "no_window" in content.lower() or "silenz" in content.lower() or "vbscript" in content.lower() or "vbs" in content.lower():
                print(f"--- {path} ---")
                lines = content.splitlines()
                for idx, line in enumerate(lines):
                    if any(w in line.lower() for w in ["create_no_window", "no_window", "silenz", "vbscript", "vbs"]):
                        print(f"  {idx+1}: {line.strip()}")
