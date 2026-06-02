import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

subagent_dir = r"C:\Users\Jonny\.gemini\antigravity\brain\04f46e99-fbc1-4971-9541-6acac7486d66"
if os.path.exists(subagent_dir):
    print("Files in subagent workspace:")
    for root, dirs, files in os.walk(subagent_dir):
        # only show files in subagent root or scratch
        for f in files:
            path = os.path.join(root, f)
            rel_path = os.path.relpath(path, subagent_dir)
            if "logs" not in rel_path and ".gemini" not in rel_path and "node_modules" not in rel_path:
                print(f"  {rel_path}: {os.path.getsize(path)} bytes")
else:
    print("Subagent workspace does not exist at:", subagent_dir)
