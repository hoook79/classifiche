import os

base_dir = r"c:\Users\Jonny\Desktop\REPORT CANZONI RADIO"
css_path = os.path.join(base_dir, "radio_charts_restyle_v2.css")
py_path = os.path.join(base_dir, "genera_html.py")

with open(css_path, "r", encoding="utf-8") as f:
    css_content = f.read()

# Double the curly braces for python f-string compatibility
# "{}" -> "{{}}"
css_doubled = css_content.replace("{", "{{").replace("}", "}}")

# We want to insert this before </style> in genera_html.py
with open(py_path, "r", encoding="utf-8") as f:
    py_content = f.read()

target = "</style>"
# Let's find the first </style> which closes the CSS block
if target in py_content:
    # Replace the FIRST occurrence of </style>
    new_style_block = f"\n\n/* === RESTYLE V2 AUTOMATICALLY APPLIED === */\n{css_doubled}\n</style>"
    py_content_new = py_content.replace(target, new_style_block, 1)
    
    with open(py_path, "w", encoding="utf-8") as f:
        f.write(py_content_new)
    print("CSS restyle successfully doubled and inserted into genera_html.py!")
else:
    print("Error: </style> tag not found in genera_html.py")
