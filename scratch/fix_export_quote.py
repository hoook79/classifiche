import os

base_dir = r"c:\Users\Jonny\Desktop\REPORT CANZONI RADIO"
py_path = os.path.join(base_dir, "genera_html.py")

with open(py_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace the single quote wrapped JS string with a backtick wrapped JS string
old_line = "    tbody.innerHTML = '<tr><td colspan=\"2\" style=\"text-align:center; padding:20px; font-weight:600; color:var(--rc-muted);\">Tutte le canzoni dell\\'export sono già presenti nella tua radio! 🎉</td></tr>';"
new_line = "    tbody.innerHTML = `<tr><td colspan=\"2\" style=\"text-align:center; padding:20px; font-weight:600; color:var(--rc-muted);\">Tutte le canzoni dell'export sono già presenti nella tua radio! 🎉</td></tr>`;"

if old_line in content:
    content = content.replace(old_line, new_line)
    print("Successfully replaced with backticks!")
else:
    # If the backslash is already parsed differently, try matching without backslash
    alt_old_line = "    tbody.innerHTML = '<tr><td colspan=\"2\" style=\"text-align:center; padding:20px; font-weight:600; color:var(--rc-muted);\">Tutte le canzoni dell'export sono già presenti nella tua radio! 🎉</td></tr>';"
    if alt_old_line in content:
        content = content.replace(alt_old_line, new_line)
        print("Successfully replaced alt with backticks!")
    else:
        print("Could not find the target line to replace.")

with open(py_path, "w", encoding="utf-8") as f:
    f.write(content)
