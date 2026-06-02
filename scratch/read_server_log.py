import os

log_file = 'server_output.log'
if os.path.exists(log_file):
    print("Log file exists! Contents:")
    with open(log_file, 'r', encoding='utf-8') as f:
        print(f.read())
else:
    print("Log file does NOT exist!")
