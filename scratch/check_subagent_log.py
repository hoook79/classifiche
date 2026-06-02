import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

log_path = r"C:\Users\Jonny\.gemini\antigravity\brain\04f46e99-fbc1-4971-9541-6acac7486d66\.system_generated\logs\transcript.jsonl"

if os.path.exists(log_path):
    print("Log file exists. Size:", os.path.getsize(log_path))
    with open(log_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    print("Total steps:", len(lines))
    # Print the last 15 lines
    for line in lines[-15:]:
        try:
            data = json.loads(line)
            print(f"Step {data.get('step_index')}: {data.get('type')} - {data.get('status')}")
            if 'content' in data and data['content']:
                print("  Content snippet:", data['content'][:200])
        except Exception as e:
            print("  Error parsing line:", e)
else:
    print("Log file does not exist at:", log_path)
