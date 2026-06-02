with open('classifica_radio.html', 'r', encoding='utf-8') as f:
    content = f.read()

targets = [
    "Voce",
    "Volevo Capire",
    "Tu cosa fai questa sera"
]

for t in targets:
    idx = content.upper().find(t.upper())
    if idx != -1:
        print(f"Found '{t}' in HTML:")
        print(content[idx-100:idx+250])
        print("---")
    else:
        print(f"'{t}' NOT found.")
