import socket
import sys

sys.stdout.reconfigure(encoding='utf-8')

port = 8000
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.bind(("127.0.0.1", port))
    print(f"Port {port} is FREE.")
except Exception as e:
    print(f"Port {port} is OCCUPIED. Error: {e}")
finally:
    s.close()
