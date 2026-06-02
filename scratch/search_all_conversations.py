import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

brain_dir = r"C:\Users\Jonny\.gemini\antigravity\brain"

if os.path.exists(brain_dir):
    print(f"Searching in brain directory: {brain_dir}")
    found_count = 0
    for folder in os.listdir(brain_dir):
        folder_path = os.path.join(brain_dir, folder)
        if os.path.isdir(folder_path):
            transcript_path = os.path.join(folder_path, ".system_generated", "logs", "transcript.jsonl")
            if os.path.exists(transcript_path):
                with open(transcript_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        try:
                            data = json.loads(line)
                            content = data.get("content", "")
                            if not content and "tool_calls" in data:
                                content = str(data["tool_calls"])
                            
                            content_lower = content.lower()
                            if "finestra dos" in content_lower or "comando silenz" in content_lower:
                                print(f"\n[{folder}] Step {data.get('step_index')} | Source: {data.get('source')}")
                                print(content[:500].strip())
                                found_count += 1
                        except:
                            pass
    print(f"\nFound {found_count} matching steps across all conversations.")
else:
    print(f"Brain directory not found at {brain_dir}")
