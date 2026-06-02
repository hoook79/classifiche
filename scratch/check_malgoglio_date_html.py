with open('classifica_radio.html', 'r', encoding='utf-8') as f:
    content = f.read()

target = "Cristiano Malgoglio"
idx = content.lower().find(target.lower())
if idx != -1:
    print("Found Malgoglio in HTML!")
    print(content[idx:idx+350])
else:
    print("Malgoglio NOT found in HTML!")
