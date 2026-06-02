import json

log_path = r"C:\Users\Jonny\.gemini\antigravity\brain\7bc56226-76b3-4e79-b3f4-6d8aab8a76f3\.system_generated\logs\transcript.jsonl"

with open(log_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

for idx in range(670, len(lines)):
    try:
        data = json.loads(lines[idx])
        if data.get('source') == 'MODEL' and data.get('type') == 'PLANNER_RESPONSE':
            print(f"\n[Step {data.get('step_index')}] MODEL PLANNER_RESPONSE:")
            print(data.get('content'))
            if data.get('tool_calls'):
                print("Tool calls:", data.get('tool_calls'))
    except Exception as e:
        pass
