with open('classifica_radio.html', 'r', encoding='utf-8') as f:
    content = f.read()

target = "FEDERICA ABBATE"
idx = content.find(target)
if idx != -1:
    print("Found Federica Abbate in classifica_radio.html!")
    snippet = content[idx:idx+300]
    print("Snippet:")
    print(snippet)
else:
    print("Federica Abbate not found in classifica_radio.html!")
