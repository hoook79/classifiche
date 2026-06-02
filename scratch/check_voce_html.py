with open('classifica_radio.html', 'r', encoding='utf-8') as f:
    content = f.read()

target = '"Voce"'
idx = 0
while True:
    idx = content.find(target, idx)
    if idx == -1:
        break
    # Print surrounding text
    snippet = content[idx-150:idx+250]
    if "Madame" in snippet or "MADAME" in snippet:
        print(f"Found Voce by Madame at index {idx}:")
        print(snippet)
        print("---")
    idx += len(target)
