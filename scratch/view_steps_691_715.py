import json

log_path = r"C:\Users\Jonny\.gemini\antigravity\brain\7bc56226-76b3-4e79-b3f4-6d8aab8a76f3\.system_generated\logs\transcript.jsonl"

with open(log_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

for idx in range(691, min(len(lines), 716)):
    try:
        data = json.loads(lines[idx])
        print(f"\n[Step {data.get('step_index')}] Source={data.get('source')}, Type={data.get('type')}, Status={data.get('status')}")
        if data.get('content'):
            print(f"Content: {data.get('content')[:200]}")
        if 'tool_calls' in data:
            print(f"Tool calls: {data['tool_calls']}")
    except Exception as e:
        pass
