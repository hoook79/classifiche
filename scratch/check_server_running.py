import socket
import sys

sys.stdout.reconfigure(encoding='utf-8')

port = 8000
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(2)
try:
    s.connect(("127.0.0.1", port))
    print(f"Success! Port {port} is open and listening.")
    s.close()
except Exception as e:
    print(f"Error! Cannot connect to port {port}: {e}")
