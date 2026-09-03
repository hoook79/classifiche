import os

base_dir = r"c:\Users\Jonny\Desktop\REPORT CANZONI RADIO"
py_path = os.path.join(base_dir, "genera_html.py")

with open(py_path, "r", encoding="utf-8") as f:
    content = f.read()

# Let's replace the single backslashes in JS newline functions with double backslashes
old_split = "  const lines = text.split('\\n');"
new_split = "  const lines = text.split('\\\\n');"

old_join1 = ").join('\\n');"
new_join1 = ").join('\\\\n');"

old_join2 = "].join('\\n');"
new_join2 = "].join('\\\\n');"

if old_split in content:
    content = content.replace(old_split, new_split)
    print("Fixed split('\\n') -> split('\\\\n')")
else:
    print("Warning: old_split not found.")

if old_join1 in content:
    content = content.replace(old_join1, new_join1)
    print("Fixed join('\\n') 1")
else:
    # Try alt format without parenthesis
    alt_join1 = ").join('\\n')"
    new_alt_join1 = ").join('\\\\n')"
    if alt_join1 in content:
        content = content.replace(alt_join1, new_alt_join1)
        print("Fixed alt join('\\n') 1")
    else:
        print("Warning: join1 not found.")

if old_join2 in content:
    content = content.replace(old_join2, new_join2)
    print("Fixed join('\\n') 2")
else:
    alt_join2 = "].join('\\n')"
    new_alt_join2 = "].join('\\\\n')"
    if alt_join2 in content:
        content = content.replace(alt_join2, new_alt_join2)
        print("Fixed alt join('\\n') 2")
    else:
        print("Warning: join2 not found.")

with open(py_path, "w", encoding="utf-8") as f:
    f.write(content)
