import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

for f in os.listdir("."):
    if "radiodate" in f.lower():
        print(f"{f}: {os.path.getsize(f)} bytes")
