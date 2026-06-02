with open('classifica_radio.html', 'r', encoding='utf-8') as f:
    content = f.read()

target = "MALGIOGLIO"
idx = content.upper().find(target.upper())
if idx != -1:
    print("Found Malgioglio in HTML!")
    print(content[idx:idx+350])
else:
    print("Malgioglio NOT found in HTML!")
