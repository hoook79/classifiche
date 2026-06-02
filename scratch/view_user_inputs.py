import json

log_path = r"C:\Users\Jonny\.gemini\antigravity\brain\7bc56226-76b3-4e79-b3f4-6d8aab8a76f3\.system_generated\logs\transcript.jsonl"

with open(log_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines in transcript: {len(lines)}")
for idx, line in enumerate(lines):
    try:
        data = json.loads(line)
        if data.get('type') == 'USER_INPUT':
            print(f"\n[Step {data.get('step_index')}] USER_INPUT:")
            print(data.get('content'))
    except Exception as e:
        pass
