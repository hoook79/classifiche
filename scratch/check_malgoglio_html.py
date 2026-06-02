with open('classifica_radio.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Let's find Malgoglio in the file
target = "CRISTIANO MALGIOGLIO"
idx = content.find(target)
if idx != -1:
    print("Found Malgoglio at position", idx)
    snippet = content[idx:idx+400]
    print("Snippet around Malgoglio:")
    print(snippet)
else:
    print("Malgoglio not found in classifica_radio.html!")
