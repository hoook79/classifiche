import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

transcript_path = r"C:\Users\Jonny\.gemini\antigravity\brain\7bc56226-76b3-4e79-b3f4-6d8aab8a76f3\.system_generated\logs\transcript.jsonl"

if os.path.exists(transcript_path):
    print("Searching user explicit messages...")
    with open(transcript_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            try:
                data = json.loads(line)
                if data.get("source") == "USER_EXPLICIT" and data.get("type") == "USER_INPUT":
                    content = data.get("content", "")
                    content_lower = content.lower()
                    if any(w in content_lower for w in ["server", "avvia", "salva", "dos", "finestra"]):
                        print(f"\n[Step {data.get('step_index', idx)}] User request:")
                        print(content)
            except Exception as e:
                pass
else:
    print(f"Transcript log not found at {transcript_path}")
