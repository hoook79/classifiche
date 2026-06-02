with open('classifica_radio.html', 'r', encoding='utf-8') as f:
    content = f.read()

for kw in ["SUPERMAN", "Abbate", "ABBATE", "Superman"]:
    idx = content.upper().find(kw.upper())
    if idx != -1:
        print(f"Found keyword '{kw}' at index {idx}")
        print(content[idx-100:idx+200])
        print("---")
    else:
        print(f"Keyword '{kw}' NOT found.")
