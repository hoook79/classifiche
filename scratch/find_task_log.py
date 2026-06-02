import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

task_dir = r"C:\Users\Jonny\.gemini\antigravity\brain\42ac35c5-af0f-4dce-9f77-646900e3521c\.system_generated\tasks"
if os.path.exists(task_dir):
    print("Files in tasks directory:")
    for f in sorted(os.listdir(task_dir)):
        print(f"  {f}: {os.path.getsize(os.path.join(task_dir, f))} bytes")
        # if task-693 is in it, print its content
        if "693" in f:
            with open(os.path.join(task_dir, f), "r", encoding="utf-8", errors="ignore") as file:
                print("--- CONTENT ---")
                print(file.read())
else:
    print("Tasks directory does not exist at:", task_dir)
