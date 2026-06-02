import json

log_path = r"C:\Users\Jonny\.gemini\antigravity\brain\7bc56226-76b3-4e79-b3f4-6d8aab8a76f3\.system_generated\logs\transcript.jsonl"

with open(log_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")
for idx in range(670, len(lines)):
    try:
        data = json.loads(lines[idx])
        if data.get('source') == 'MODEL' and data.get('type') == 'PLANNER_RESPONSE' and not data.get('tool_calls'):
            print(f"\n[Step {data.get('step_index')}] Assistant Final Response:")
            print(data.get('content'))
    except Exception as e:
        pass
